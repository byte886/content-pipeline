package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/elazarl/goproxy"
)

// 公众号历史页（profile_ext action=home）自动翻 getmsg 全量导出。
// 凭证（key/appmsg_token/pass_ticket）短时效且绑定微信客户端环境，事后用 curl 复现必然
// 失败，因此必须在客户端 home 会话内、秒级由代理自动发起翻页，复用 home 的完整参数与 UA。

var (
	mpHomeTriggered sync.Map
	mpAppmsgTokenRe = regexp.MustCompile(`window\.appmsg_token\s*=\s*"([^"]+)"`)
	mpNextOffsetRe  = regexp.MustCompile(`var next_offset\s*=\s*"([^"]*)"`)
	// 服务端把凭证渲染进 HTML：var key/uin/pass_ticket = "..."
	mpVarCredRe = regexp.MustCompile(`var (key|uin|pass_ticket)\s*=\s*"([^"]*)"`)
)

// articleExportHandler 作为独立 OnResponse handler 注册（不改写主 onResponse）
func (c *Captor) articleExportHandler(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	c.maybeAutoExportArticles(resp)
	return resp
}

// apiLogf 向 API 日志追加一行导出进度
func (c *Captor) apiLogf(f string, a ...interface{}) {
	if c.apiLogFile == nil {
		return
	}
	c.apiLogFile.WriteString(fmt.Sprintf("[%s MP_EXPORT] %s\n",
		time.Now().Format("15:04:05"), fmt.Sprintf(f, a...)))
	c.apiLogFile.Sync()
}

func (c *Captor) maybeAutoExportArticles(resp *http.Response) {
	if resp == nil || resp.Request == nil || resp.Body == nil {
		return
	}
	rq := resp.Request
	if !strings.HasSuffix(rq.Host, "mp.weixin.qq.com") ||
		!strings.Contains(rq.URL.Path, "/mp/profile_ext") ||
		rq.URL.Query().Get("action") != "home" {
		return
	}
	bodyb, err := io.ReadAll(resp.Body)
	if err != nil {
		return
	}
	resp.Body = io.NopCloser(bytes.NewReader(bodyb))
	bodyStr := string(bodyb)

	m := mpAppmsgTokenRe.FindStringSubmatch(bodyStr)
	if m == nil {
		c.apiLogf("home 响应无 appmsg_token（可能是提示页，len=%d）", len(bodyb))
		return
	}
	appmsgToken := m[1]
	base, err := url.ParseQuery(rq.URL.RawQuery)
	if err != nil {
		return
	}
	// 构造的 home 链接 URL 里通常只有 __biz；服务端把 uin/key/pass_ticket 渲染进
	// HTML 的全局变量，从响应补全，否则 getmsg 缺凭证会空返回。
	for _, cv := range mpVarCredRe.FindAllStringSubmatch(bodyStr, -1) {
		if base.Get(cv[1]) == "" && cv[2] != "" {
			base.Set(cv[1], cv[2])
		}
	}
	triggerID := base.Get("__biz") + "|" + appmsgToken
	if _, loaded := mpHomeTriggered.LoadOrStore(triggerID, true); loaded {
		return
	}
	c.apiLogf("检测到 home 历史页（biz=%s key=%t uin=%s pass_ticket=%t len=%d），启动自动翻 getmsg",
		base.Get("__biz"), base.Get("key") != "", base.Get("uin"),
		base.Get("pass_ticket") != "", len(bodyb))
	go c.runArticleExport(rq, base, appmsgToken, bodyStr)
}

type mpCommInfo struct {
	Datetime int64 `json:"datetime"`
	Type     int   `json:"type"`
	FakeID   int64 `json:"fakeid"`
}

type mpSubItem struct {
	Title      string `json:"title"`
	ContentURL string `json:"content_url"`
	Digest     string `json:"digest"`
	Cover      string `json:"cover"`
}

type mpExtInfo struct {
	Title      string      `json:"title"`
	ContentURL string      `json:"content_url"`
	Digest     string      `json:"digest"`
	Cover      string      `json:"cover"`
	IsMulti    int         `json:"is_multi"`
	Multi      []mpSubItem `json:"multi_app_msg_item_list"`
}

type mpGenItem struct {
	Comm mpCommInfo `json:"comm_msg_info"`
	Ext  mpExtInfo  `json:"app_msg_ext_info"`
}

type mpIndexItem struct {
	Seq      int         `json:"seq"`
	Datetime int64       `json:"datetime"`
	Type     int         `json:"type"`
	Title    string      `json:"title"`
	URL      string      `json:"url"`
	Digest   string      `json:"digest"`
	Subs     []mpSubItem `json:"subs,omitempty"`
}

func parseGeneralList(s string) ([]mpGenItem, error) {
	var wrap struct {
		List []mpGenItem `json:"list"`
	}
	if err := json.Unmarshal([]byte(s), &wrap); err != nil {
		return nil, err
	}
	return wrap.List, nil
}

func safeMpName(s string) string {
	return strings.NewReplacer("=", "", "/", "_", "+", "-", "%", "").Replace(s)
}

func (c *Captor) runArticleExport(rq *http.Request, base url.Values, appmsgToken, homeBody string) {
	biz := base.Get("__biz")
	dir := filepath.Join(filepath.Dir(c.outputFile), "mp_articles_"+safeMpName(biz))
	if err := os.MkdirAll(dir, 0755); err != nil {
		c.apiLogf("建目录失败 %v", err)
		return
	}
	ua := rq.Header.Get("User-Agent")
	homeURL := "https://mp.weixin.qq.com" + rq.URL.RequestURI()

	// 独立 transport：显式走上游（出口与 home 一致）或直连；绝不回环到系统代理 8899。
	tr := &http.Transport{
		TLSHandshakeTimeout: 20 * time.Second,
		IdleConnTimeout:     30 * time.Second,
	}
	if c.upstreamProxy != "" && checkProxyAvailable(c.upstreamProxy) {
		if u, err := url.Parse(c.upstreamProxy); err == nil {
			tr.Proxy = http.ProxyURL(u)
		}
	}
	client := &http.Client{Transport: tr, Timeout: 30 * time.Second}

	offset := ""
	if mm := mpNextOffsetRe.FindStringSubmatch(homeBody); mm != nil {
		offset = mm[1]
	}
	if offset == "" {
		offset = "0"
	}

	var index []mpIndexItem
	seq, page := 0, 0
	const maxPages = 200
	for ; page < maxPages; page++ {
		v := url.Values{}
		for k, vs := range base {
			cp := make([]string, len(vs))
			copy(cp, vs)
			v[k] = cp
		}
		v.Set("action", "getmsg")
		v.Set("f", "json")
		v.Set("offset", offset)
		v.Set("count", "10")
		v.Set("is_ok", "1")
		v.Set("appmsg_token", appmsgToken)
		v.Set("wxtoken", "")
		v.Set("x5", "1")
		getURL := "https://mp.weixin.qq.com/mp/profile_ext?" + v.Encode()
		req, _ := http.NewRequest("GET", getURL, nil)
		req.Header.Set("User-Agent", ua)
		req.Header.Set("Referer", homeURL)
		req.Header.Set("X-Requested-With", "XMLHttpRequest")
		if ck := rq.Header.Get("Cookie"); ck != "" {
			req.Header.Set("Cookie", ck)
		}
		if k := base.Get("key"); k != "" {
			req.Header.Set("X-WECHAT-KEY", k)
		}
		if u := base.Get("uin"); u != "" {
			req.Header.Set("X-WECHAT-UIN", u)
		}
		resp, err := client.Do(req)
		if err != nil {
			c.apiLogf("getmsg page=%d 请求失败 %v", page, err)
			break
		}
		pb, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		os.WriteFile(filepath.Join(dir, fmt.Sprintf("page_%03d.json", page)), pb, 0644)

		var d struct {
			Ret            int         `json:"ret"`
			ErrMsg         string      `json:"errmsg"`
			MsgCount       int         `json:"msg_count"`
			CanMsgContinue int         `json:"can_msg_continue"`
			NextOffset     json.Number `json:"next_offset"`
			GeneralMsgList string      `json:"general_msg_list"`
			BaseResp       struct {
				Ret    int    `json:"ret"`
				ErrMsg string `json:"errmsg"`
			} `json:"base_resp"`
		}
		if err := json.Unmarshal(pb, &d); err != nil {
			n := 120
			if len(pb) < n {
				n = len(pb)
			}
			c.apiLogf("page=%d 非JSON: %s", page, string(pb[:n]))
			break
		}
		ret := d.Ret
		if ret == 0 {
			ret = d.BaseResp.Ret
		}
		if ret != 0 {
			c.apiLogf("page=%d 服务端返回 ret=%d errmsg=%s（凭证可能过期）", page, ret, d.ErrMsg)
			break
		}
		gl, err := parseGeneralList(d.GeneralMsgList)
		if err != nil {
			c.apiLogf("page=%d general_msg_list 解析失败 %v", page, err)
			break
		}
		for _, it := range gl {
			item := mpIndexItem{
				Seq: seq, Datetime: it.Comm.Datetime, Type: it.Comm.Type,
				Title: it.Ext.Title, URL: it.Ext.ContentURL, Digest: it.Ext.Digest,
				Subs: it.Ext.Multi,
			}
			index = append(index, item)
			seq++
		}
		c.apiLogf("page=%d 本页%d 累计%d continue=%d next=%s",
			page, len(gl), seq, d.CanMsgContinue, d.NextOffset.String())
		if d.CanMsgContinue == 0 {
			break
		}
		offset = d.NextOffset.String()
		time.Sleep(350 * time.Millisecond)
	}

	jb, _ := json.MarshalIndent(index, "", "  ")
	os.WriteFile(filepath.Join(dir, "articles_index.json"), jb, 0644)
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("公众号 biz=%s 文章总数=%d 翻页数=%d 导出时间=%s\n",
		biz, seq, page+1, time.Now().Format("2006-01-02 15:04:05")))
	for _, it := range index {
		sb.WriteString(fmt.Sprintf("%03d %s %s\n",
			it.Seq, time.Unix(it.Datetime, 0).Format("2006-01-02"), it.Title))
	}
	os.WriteFile(filepath.Join(dir, "articles_titles.txt"), []byte(sb.String()), 0644)
	c.apiLogf("完成：文章总数=%d 翻页=%d 目录=%s", seq, page+1, dir)
}
