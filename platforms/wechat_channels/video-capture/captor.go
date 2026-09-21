package main

import (
	"bytes"
	"compress/gzip"
	"crypto/md5"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"log"
	"math/big"
	"net"
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

// getCertDir 返回可执行文件所在目录，证书与二进制同目录
func getCertDir() string {
	exe, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(exe)
}

// VideoInfo 视频信息
type VideoInfo struct {
	ID          string            `json:"id"`
	URL         string            `json:"url"`
	CoverURL    string            `json:"cover_url"`
	Size        int64             `json:"size"`
	Description string            `json:"description"`
	ShortTitle  string            `json:"short_title"`
	Duration    int               `json:"duration"`
	Width       int               `json:"width"`
	Height      int               `json:"height"`
	MD5         string            `json:"md5"`
	Classify    string            `json:"classify"`
	Suffix      string            `json:"suffix"`
	DecodeKey   string            `json:"decode_key"`
	Account     string            `json:"account"`
	OtherData   map[string]string `json:"other_data"`
	CapturedAt  string            `json:"captured_at"`
}

// Captor 视频捕获器
type Captor struct {
	port          int
	outputFile    string
	autoDownload  bool
	downloadDir   string
	upstreamProxy string
	autoScroll    bool
	replayList    bool
	shortProbe    bool
	proxy         *goproxy.ProxyHttpServer
	server        *http.Server
	videos        map[string]*VideoInfo
	videosMux     sync.RWMutex
	mediaMark     sync.Map
	version       string
	apiLogFile    *os.File
}

var (
	qqMediaRegex   = regexp.MustCompile(`get\s*media\(\)\{`)
	qqCommentRegex = regexp.MustCompile(`async\s*finderGetCommentDetail\((\w+)\)\s*\{return(.*?)\s*}\s*async`)
)

// NewCaptor 创建捕获器
func NewCaptor(port int, outputFile string, autoDownload bool, downloadDir string, upstreamProxy string, autoScroll bool, replayList bool, shortProbe bool) (*Captor, error) {
	c := &Captor{
		port:          port,
		outputFile:    outputFile,
		autoDownload:  autoDownload,
		downloadDir:   downloadDir,
		upstreamProxy: upstreamProxy,
		autoScroll:    autoScroll,
		replayList:    replayList,
		shortProbe:    shortProbe,
		videos:        make(map[string]*VideoInfo),
		version:       "1.0.0",
	}

	// 加载已有视频
	if err := c.loadVideos(); err != nil {
		log.Printf("加载已有视频失败: %v", err)
	}

	// 打开API日志文件
	apiLogPath := strings.Replace(outputFile, ".json", "_api.log", 1)
	if apiLogPath == outputFile {
		apiLogPath = outputFile + "_api.log"
	}
	f, err := os.OpenFile(apiLogPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Printf("打开API日志文件失败: %v", err)
	} else {
		c.apiLogFile = f
		log.Printf("API日志: %s", apiLogPath)
	}

	// 初始化代理
	if err := c.initProxy(); err != nil {
		return nil, err
	}

	return c, nil
}

// initProxy 初始化代理
func (c *Captor) initProxy() error {
	// 加载或生成CA证书（优先使用已有证书，避免每次启动都变导致信任失效）
	ca, err := c.loadOrGenerateCA()
	if err != nil {
		return fmt.Errorf("加载/生成CA证书失败: %w", err)
	}

	goproxy.GoproxyCa = *ca
	goproxy.OkConnect = &goproxy.ConnectAction{Action: goproxy.ConnectAccept, TLSConfig: goproxy.TLSConfigFromCA(ca)}
	goproxy.MitmConnect = &goproxy.ConnectAction{Action: goproxy.ConnectMitm, TLSConfig: goproxy.TLSConfigFromCA(ca)}
	goproxy.HTTPMitmConnect = &goproxy.ConnectAction{Action: goproxy.ConnectHTTPMitm, TLSConfig: goproxy.TLSConfigFromCA(ca)}
	goproxy.RejectConnect = &goproxy.ConnectAction{Action: goproxy.ConnectReject, TLSConfig: goproxy.TLSConfigFromCA(ca)}

	c.proxy = goproxy.NewProxyHttpServer()
	c.proxy.Verbose = true

	// 设置传输
	transport := &http.Transport{
		DisableKeepAlives: false,
		DialContext: (&net.Dialer{
			Timeout: 60 * time.Second,
		}).DialContext,
		TLSHandshakeTimeout:   60 * time.Second,
		ResponseHeaderTimeout: 60 * time.Second,
		IdleConnTimeout:       30 * time.Second,
	}

	// 设置上游代理（如ClashX），实现规则路由
	if c.upstreamProxy != "" {
		// 先检查上游代理是否可用
		if !checkProxyAvailable(c.upstreamProxy) {
			log.Printf("⚠️  上游代理不可用 (%s)，将自动降级为直连模式", c.upstreamProxy)
			log.Printf("   请确认ClashX已启动并监听对应端口，或使用 -upstream \"\" 禁用上游代理")
		} else {
			proxyURL, err := url.Parse(c.upstreamProxy)
			if err != nil {
				log.Printf("上游代理URL解析失败(%s)，将直连: %v", c.upstreamProxy, err)
			} else {
				transport.Proxy = http.ProxyURL(proxyURL)
				fmt.Printf("上游代理已设置: %s (国内直连/国外自动VPN)\n", c.upstreamProxy)
			}
		}
	}

	c.proxy.Tr = transport

	// 对所有HTTPS进行MITM
	c.proxy.OnRequest().HandleConnectFunc(func(host string, ctx *goproxy.ProxyCtx) (*goproxy.ConnectAction, string) {
		return goproxy.MitmConnect, host
	})

	// 请求处理
	c.proxy.OnRequest().DoFunc(c.onRequest)
	// 响应处理
	c.proxy.OnResponse().DoFunc(c.onResponse)

	return nil
}

// loadOrGenerateCA 加载已有CA证书，不存在则生成新的
// 证书路径：相对于可执行文件的目录（与二进制同目录），避免从项目根目录运行时生成新证书
func (c *Captor) loadOrGenerateCA() (*tls.Certificate, error) {
	certDir := getCertDir()
	certPath := filepath.Join(certDir, "ca.crt")
	keyPath := filepath.Join(certDir, "ca.key")

	// 尝试加载已有证书
	if _, err := os.Stat(certPath); err == nil {
		if _, err := os.Stat(keyPath); err == nil {
			certPEM, err1 := os.ReadFile(certPath)
			keyPEM, err2 := os.ReadFile(keyPath)
			if err1 == nil && err2 == nil {
				cert, err := tls.X509KeyPair(certPEM, keyPEM)
				if err == nil {
					if cert.Leaf, err = x509.ParseCertificate(cert.Certificate[0]); err == nil {
						fmt.Printf("已加载CA证书: %s\n", certPath)
						return &cert, nil
					}
				}
			}
		}
	}
	// 不存在或加载失败，生成新证书
	return c.generateCA()
}

// generateCA 生成自签名CA证书，保存在可执行文件同目录
func (c *Captor) generateCA() (*tls.Certificate, error) {
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}

	template := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			Organization: []string{"Video Capture CA"},
			CommonName:   "Video Capture CA",
		},
		NotBefore:             time.Now().Add(-time.Hour),
		NotAfter:              time.Now().Add(10 * 365 * 24 * time.Hour),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
		IsCA:                  true,
	}

	derBytes, err := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
	if err != nil {
		return nil, err
	}

	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: derBytes})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(priv)})

	// 保存CA证书到可执行文件同目录
	certDir := getCertDir()
	certPath := filepath.Join(certDir, "ca.crt")
	keyPath := filepath.Join(certDir, "ca.key")
	os.WriteFile(certPath, certPEM, 0644)
	os.WriteFile(keyPath, keyPEM, 0600)
	fmt.Printf("CA证书已生成: %s\n", certPath)
	fmt.Println("请在系统钥匙串中信任此证书")

	cert, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		return nil, err
	}

	if cert.Leaf, err = x509.ParseCertificate(cert.Certificate[0]); err != nil {
		return nil, err
	}

	return &cert, nil
}

// Start 启动代理服务器
func (c *Captor) Start() error {
	addr := fmt.Sprintf("127.0.0.1:%d", c.port)
	c.server = &http.Server{
		Addr:    addr,
		Handler: c.proxy,
	}

	fmt.Printf("代理服务器已启动: %s\n", addr)
	return c.server.ListenAndServe()
}

// Stop 停止代理
func (c *Captor) Stop() {
	if c.server != nil {
		c.server.Close()
	}
	if c.apiLogFile != nil {
		c.apiLogFile.Close()
	}
	c.saveVideos()
}

// onRequest 请求处理
func (c *Captor) onRequest(r *http.Request, ctx *goproxy.ProxyCtx) (*http.Request, *http.Response) {
	// 记录所有微信相关请求（公众号主页/视频号API/文章列表）
	host := r.Host
	if strings.HasSuffix(host, "weixin.qq.com") ||
		strings.HasSuffix(host, "qq.com") ||
		strings.Contains(host, "weixin") ||
		strings.Contains(host, "wx.qq.com") {
		c.logAPIRequest(r)
	}

	// 禁用公众号主页缓存，确保注入的JS每次都执行
	if strings.HasSuffix(host, "channels.weixin.qq.com") &&
		strings.Contains(r.URL.Path, "/web/pages/mp_profile") {
		r.Header.Set("Cache-Control", "no-cache, no-store, must-revalidate")
		r.Header.Set("Pragma", "no-cache")
		r.Header.Set("If-Modified-Since", "")
		r.Header.Set("If-None-Match", "")
	}

	// 处理微信视频号的回调请求
	if strings.Contains(r.Host, "qq.com") && strings.Contains(r.URL.Path, "/res-downloader/wechat") {
		return c.handleWechatRequest(r)
	}
	return r, nil
}

// logAPIRequest 记录API请求
func (c *Captor) logAPIRequest(r *http.Request) {
	if c.apiLogFile == nil {
		return
	}

	entry := fmt.Sprintf("[%s] %s %s%s\n",
		time.Now().Format("2006-01-02 15:04:05"),
		r.Method,
		r.Host,
		r.URL.RequestURI(),
	)

	// 显式记录Cookie（Go的http.Request.Header中Cookie是单独处理的）
	if len(r.Cookies()) > 0 {
		cookieStr := ""
		for _, cookie := range r.Cookies() {
			cookieStr += cookie.Name + "=" + cookie.Value + "; "
		}
		entry += fmt.Sprintf("  Cookies: %s\n", cookieStr)
	}

	// 记录请求头
	entry += fmt.Sprintf("  Headers: %v\n", r.Header)

	// 记录请求体（如果是POST）
	if r.Method == "POST" && r.Body != nil {
		body, err := io.ReadAll(r.Body)
		if err == nil && len(body) > 0 {
			entry += fmt.Sprintf("  Body: %s\n", string(body))
			// 恢复请求体
			r.Body = io.NopCloser(strings.NewReader(string(body)))
		}
	}

	entry += "\n"

	c.apiLogFile.WriteString(entry)
	c.apiLogFile.Sync()
}

// onResponse 响应处理
func (c *Captor) onResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	if resp == nil || resp.Request == nil {
		return resp
	}

	host := resp.Request.Host
	path := resp.Request.URL.Path

	// 记录所有微信相关响应（方案B研究）
	if strings.HasSuffix(host, "weixin.qq.com") ||
		strings.HasSuffix(host, "qq.com") ||
		strings.Contains(host, "weixin") ||
		strings.Contains(host, "wx.qq.com") {
		c.logAPIResponse(resp)
	}

	// 视频号页面 - 仅在 -autoscroll 开启时注入自动滚动JS；关闭时页面保持静止，
	// 但响应体仍由上方 logAPIResponse 完整记录，可手动滚动控制采集节奏。
	if c.replayList && strings.HasSuffix(host, "channels.weixin.qq.com") &&
		strings.Contains(path, "/web/pages/profile") {
		return c.injectReplayListHook(resp)
	}
	if c.autoScroll && strings.HasSuffix(host, "channels.weixin.qq.com") &&
		(strings.Contains(path, "/web/pages/feed") || strings.Contains(path, "/web/pages/home") ||
			strings.Contains(path, "/web/pages/profile")) {
		return c.injectVideoFeedHook(resp)
	}

	// 短视频播放换签探针（静默：不自动滚动、不自动点击；滚动与点开播放由人工控制）。
	// 覆盖 profile（列表/弹层）与 feed/home（可能的独立播放页 document），抓播放瞬间的签名直链。
	if c.shortProbe && strings.HasSuffix(host, "channels.weixin.qq.com") &&
		(strings.Contains(path, "/web/pages/profile") || strings.Contains(path, "/web/pages/feed") ||
			strings.Contains(path, "/web/pages/home")) {
		return c.injectShortProbeHook(resp)
	}

	// 公众号主页(mp_profile) - 注入文章列表提取JS
	if strings.HasSuffix(host, "channels.weixin.qq.com") &&
		strings.Contains(path, "/web/pages/mp_profile") {
		return c.injectArticleListHook(resp)
	}

	// 文章详情页 - 注入JS捕获appmsg_token等参数
	if strings.HasSuffix(host, "mp.weixin.qq.com") &&
		strings.HasPrefix(path, "/s") {
		return c.injectArticleDetailHook(resp)
	}

	// 微信JS资源 - 注入Hook代码
	if strings.HasSuffix(host, "res.wx.qq.com") {
		if strings.Contains(path, "web/web-finder/res/js/virtual_svg-icons-register.publish") {
			return c.injectVideoHook(resp)
		}
		if strings.HasSuffix(resp.Request.URL.RequestURI(), fmt.Sprintf(".js?v=%s", c.version)) {
			return c.replaceWxJsContent(resp, ".js\"", fmt.Sprintf(".js?v=%s\"", c.version))
		}
	}

	return resp
}

// logAPIResponse 记录API响应
func (c *Captor) logAPIResponse(resp *http.Response) {
	if c.apiLogFile == nil || resp.Body == nil {
		return
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return
	}
	// 恢复响应体
	resp.Body = io.NopCloser(strings.NewReader(string(body)))

	entry := fmt.Sprintf("[%s] RESPONSE %s %s%s (status=%d, len=%d)\n",
		time.Now().Format("2006-01-02 15:04:05"),
		resp.Request.Method,
		resp.Request.Host,
		resp.Request.URL.RequestURI(),
		resp.StatusCode,
		len(body),
	)

	// 记录响应体。视频号列表API/页面内嵌JSON必须完整记录（含视频URL、类型、标题），
	// 其余JSON/文本只记录前2000字符避免日志过大。
	contentType := resp.Header.Get("Content-Type")
	host := resp.Request.Host
	bodyStr := string(body)
	isVideoData := strings.Contains(host, "channels.weixin.qq.com") ||
		strings.Contains(bodyStr, "stodownload?encfilekey=") ||
		strings.Contains(bodyStr, "finder.video.qq.com") ||
		strings.Contains(bodyStr, "finderUserName") ||
		strings.Contains(bodyStr, "liveReplay") || strings.Contains(bodyStr, "live_replay")
	if strings.Contains(contentType, "json") || strings.Contains(contentType, "text") ||
		strings.Contains(contentType, "javascript") || strings.Contains(contentType, "html") {
		const fullCap = 20 * 1024 * 1024
		if isVideoData && len(body) > 2000 {
			limit := len(body)
			if limit > fullCap {
				limit = fullCap
			}
			entry += fmt.Sprintf("  Body(FULL len=%d): %s\n", len(body), bodyStr[:limit])
		} else if len(body) > 2000 {
			entry += fmt.Sprintf("  Body: %s...(truncated)\n", bodyStr[:2000])
		} else {
			entry += fmt.Sprintf("  Body: %s\n", bodyStr)
		}
	} else {
		entry += fmt.Sprintf("  Content-Type: %s (not logged)\n", contentType)
	}

	entry += "\n"
	c.apiLogFile.WriteString(entry)
	c.apiLogFile.Sync()
}

// handleWechatRequest 处理微信视频号的回调
func (c *Captor) handleWechatRequest(r *http.Request) (*http.Request, *http.Response) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return r, c.buildEmptyResponse(r)
	}

	// 检查是否是文章列表回调(type=3)
	if strings.Contains(r.URL.RawQuery, "type=3") {
		c.handleArticleList(body)
		return r, c.buildEmptyResponse(r)
	}

	go c.handleMedia(body)

	return r, c.buildEmptyResponse(r)
}

// handleArticleList 处理文章列表回调
func (c *Captor) handleArticleList(body []byte) {
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return
	}

	msgType, _ := result["type"].(string)
	page, _ := result["page"].(string)
	if page == "" {
		page, _ = result["url"].(string)
	}

	// 处理文章详情页参数回调
	if msgType == "article_detail_params" {
		appmsgToken, _ := result["appmsg_token"].(string)
		uin, _ := result["uin"].(string)
		key, _ := result["key"].(string)
		passTicket, _ := result["pass_ticket"].(string)
		wxtoken, _ := result["wxtoken"].(string)
		biz, _ := result["biz"].(string)
		reason, _ := result["reason"].(string)
		
		entry := fmt.Sprintf("[%s] ARTICLE_DETAIL_PARAMS reason=%s\n  appmsg_token=%s\n  uin=%s\n  key=%s\n  pass_ticket=%s\n  wxtoken=%s\n  biz=%s\n  url=%s\n",
			time.Now().Format("2006-01-02 15:04:05"),
			reason, appmsgToken, uin, key, passTicket, wxtoken, biz, page)
		if c.apiLogFile != nil {
			c.apiLogFile.WriteString(entry)
			c.apiLogFile.Sync()
		}
		if appmsgToken != "" {
			fmt.Printf("[%s] ★★★ 捕获到appmsg_token: %s (reason=%s)\n", time.Now().Format("15:04:05"), appmsgToken, reason)
		} else {
			fmt.Printf("[%s] appmsg_token为空 (reason=%s)\n", time.Now().Format("15:04:05"), reason)
		}
		return
	}

	if msgType == "page_html" {
		html, _ := result["html"].(string)
		entry := fmt.Sprintf("[%s] PAGE_HTML len=%d url=%s\n%s\n",
			time.Now().Format("2006-01-02 15:04:05"),
			len(html), page, html)
		if c.apiLogFile != nil {
			c.apiLogFile.WriteString(entry)
			c.apiLogFile.Sync()
		}
		fmt.Printf("[%s] 收到页面HTML, 长度=%d\n", time.Now().Format("15:04:05"), len(html))
		return
	}

	if msgType == "articles" {
		articles, ok := result["articles"].([]interface{})
		bodyText, _ := result["bodyText"].(string)

		if ok && len(articles) > 0 {
			for _, item := range articles {
				article, ok := item.(map[string]interface{})
				if !ok {
					continue
				}
				title, _ := article["title"].(string)
				url, _ := article["url"].(string)
				if title == "" || url == "" {
					continue
				}
				entry := fmt.Sprintf("[%s] ARTICLE_LIST title=%s url=%s page=%s\n",
					time.Now().Format("2006-01-02 15:04:05"),
					title, url, page)
				if c.apiLogFile != nil {
					c.apiLogFile.WriteString(entry)
					c.apiLogFile.Sync()
				}
				fmt.Printf("[%s] 捕获到文章: %s\n", time.Now().Format("15:04:05"), truncate(title, 50))
			}
		}

		if bodyText != "" {
			entry := fmt.Sprintf("[%s] BODY_TEXT len=%d\n%s\n",
				time.Now().Format("2006-01-02 15:04:05"),
				len(bodyText), bodyText)
			if c.apiLogFile != nil {
				c.apiLogFile.WriteString(entry)
				c.apiLogFile.Sync()
			}
		}
	}
}

// handleMedia 处理视频媒体信息
func (c *Captor) handleMedia(body []byte) {
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return
	}

	mediaArr, ok := result["media"].([]interface{})
	if !ok || len(mediaArr) == 0 {
		return
	}

	firstMedia, ok := mediaArr[0].(map[string]interface{})
	if !ok {
		return
	}

	rawURL, ok := firstMedia["url"].(string)
	if !ok || rawURL == "" {
		return
	}

	// 优先使用md5sum作为唯一标识，没有则用URL
	uniqueKey := rawURL
	if md5sum, ok := firstMedia["md5sum"].(string); ok && md5sum != "" {
		uniqueKey = md5sum
	}

	urlSign := md5Hash(uniqueKey)
	if _, loaded := c.mediaMark.Load(urlSign); loaded {
		return
	}

	// 构建视频信息
	video := &VideoInfo{
		ID:         urlSign[:16],
		URL:        rawURL,
		Classify:   "video",
		Suffix:     ".mp4",
		OtherData:  make(map[string]string),
		CapturedAt: time.Now().Format("2006-01-02 15:04:05"),
	}

	// 处理图片类型
	if mediaType, ok := firstMedia["mediaType"].(float64); ok && mediaType == 9 {
		video.Classify = "image"
		video.Suffix = ".png"
	}

	// URL Token
	if urlToken, ok := firstMedia["urlToken"].(string); ok {
		video.URL += urlToken
	}

	// 文件大小（优先cdnFileSize，其次fileSize）
	if cdnSize, ok := firstMedia["cdnFileSize"].(float64); ok && cdnSize > 0 {
		video.Size = int64(cdnSize)
	} else {
		switch size := firstMedia["fileSize"].(type) {
		case float64:
			video.Size = int64(size)
		case string:
			fmt.Sscanf(size, "%d", &video.Size)
		}
	}

	// 封面URL
	if coverURL, ok := firstMedia["coverUrl"].(string); ok {
		video.CoverURL = coverURL
	}

	// 解密密钥
	if decodeKey, ok := firstMedia["decodeKey"].(string); ok {
		video.DecodeKey = decodeKey
	}

	// 描述（标题）
	if desc, ok := result["description"].(string); ok {
		video.Description = strings.TrimSpace(desc)
	}

	// 短标题
	if shortTitles, ok := result["shortTitle"].([]interface{}); ok && len(shortTitles) > 0 {
		if st, ok := shortTitles[0].(map[string]interface{}); ok {
			if title, ok := st["shortTitle"].(string); ok {
				video.ShortTitle = strings.TrimSpace(title)
			}
		}
	}

	// 视频时长
	if duration, ok := firstMedia["videoPlayLen"].(float64); ok {
		video.Duration = int(duration)
	}

	// 分辨率
	if width, ok := firstMedia["width"].(float64); ok {
		video.Width = int(width)
	}
	if height, ok := firstMedia["height"].(float64); ok {
		video.Height = int(height)
	}

	// MD5唯一标识
	if md5sum, ok := firstMedia["md5sum"].(string); ok {
		video.MD5 = md5sum
	}

	// 视频格式（多种清晰度）
	if spec, ok := firstMedia["spec"].([]interface{}); ok {
		var formats []string
		var maxBitrate int64 = 0
		var bestFormat string
		for _, item := range spec {
			if m, ok := item.(map[string]interface{}); ok {
				if format, ok := m["fileFormat"].(string); ok {
					formats = append(formats, format)
				}
				// 找最高清晰度
				if bitrate, ok := m["videoBitrate"].(float64); ok {
					if int64(bitrate) > maxBitrate {
						maxBitrate = int64(bitrate)
						if f, ok := m["fileFormat"].(string); ok {
							bestFormat = f
						}
					}
				}
			}
		}
		video.OtherData["wx_file_formats"] = strings.Join(formats, "#")
		if bestFormat != "" {
			video.OtherData["best_format"] = bestFormat
		}
	}

	c.mediaMark.Store(urlSign, true)

	// 保存视频
	c.videosMux.Lock()
	c.videos[urlSign] = video
	count := len(c.videos)
	c.videosMux.Unlock()

	// 立即保存到文件
	c.saveVideos()

	title := video.ShortTitle
	if title == "" {
		title = video.Description
	}
	fmt.Printf("[%s] 捕获到新%s: %s (时长:%ds 分辨率:%dx%d)\n",
		time.Now().Format("15:04:05"), video.Classify, truncate(title, 50),
		video.Duration, video.Width, video.Height)
	fmt.Printf("  总计: %d 个资源\n", count)

	// 自动下载
	if c.autoDownload && video.Classify == "video" {
		go c.downloadVideo(video)
	}
}

// injectArticleListHook 注入文章列表提取JS（公众号主页）
func (c *Captor) injectArticleListHook(resp *http.Response) *http.Response {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp
	}

	bodyStr := string(body)

	// 在</body>前注入文章列表提取脚本
	articleHookJS := `
<script>
(function() {
  console.log('[ArticleHook] 脚本已注入');
  
  var lastSent = 0;
  
  // 发送页面HTML到代理，用于调试DOM结构
  function sendPageHTML(reason) {
    var now = Date.now();
    if (now - lastSent < 500) return; // 限流：最多每秒2次
    lastSent = now;
    
    var html = document.documentElement.outerHTML.substring(0, 100000);
    var bodyText = document.body ? document.body.innerText.substring(0, 10000) : '';
    var allText = document.body ? document.body.textContent.substring(0, 10000) : '';
    
    // 获取所有可见文本
    var visibleText = '';
    try {
      var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
      var node;
      var count = 0;
      while (node = walker.nextNode()) {
        if (node.textContent && node.textContent.trim()) {
          visibleText += node.textContent.trim() + ' | ';
          count++;
          if (count > 100) break;
        }
      }
    } catch(e) {}
    
    fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3', {
      method: 'POST',
      mode: 'no-cors',
      body: JSON.stringify({
        type: 'page_html', 
        html: html, 
        bodyText: bodyText,
        allText: allText,
        visibleText: visibleText,
        url: location.href,
        title: document.title,
        reason: reason || 'periodic'
      })
    });
  }
  
  // 提取文章列表
  function extractArticles() {
    var articles = [];
    
    // 尝试多种选择器匹配文章列表
    var selectors = [
      'a[href*="/s/"]',
      'a[href*="mp.weixin.qq.com"]',
      '.article-item',
      '.feed-item',
      '.list-item',
      '[class*="article"]',
      '[class*="feed"]',
      '[class*="item"]'
    ];
    
    var seen = new Set();
    selectors.forEach(function(selector) {
      try {
        var elements = document.querySelectorAll(selector);
        elements.forEach(function(el) {
          var title = '';
          var url = '';
          
          if (el.tagName === 'A') {
            url = el.href || '';
            title = el.textContent || el.innerText || '';
          } else {
            var link = el.querySelector('a');
            if (link) {
              url = link.href || '';
            }
            title = el.textContent || el.innerText || '';
          }
          
          title = title.trim().substring(0, 200);
          if (title && url && title.length > 5 && !seen.has(url)) {
            seen.add(url);
            articles.push({title: title, url: url});
          }
        });
      } catch(e) {}
    });
    
    if (articles.length > 0) {
      fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3', {
        method: 'POST',
        mode: 'no-cors',
        body: JSON.stringify({type: 'articles', articles: articles, url: location.href})
      });
    }
  }

  // 页面加载完成后开始提取
  function start() {
    console.log('[ArticleHook] 页面加载完成，开始提取');
    
    // 发送页面基本信息
    function sendPageInfo(reason) {
      var now = Date.now();
      if (now - lastSent < 1000) return;
      lastSent = now;
      
      var html = document.documentElement.outerHTML.substring(0, 100000);
      var bodyText = document.body ? document.body.innerText.substring(0, 10000) : '';
      
      // 查找所有可点击元素
      var clickables = [];
      document.querySelectorAll('a, button, [role="button"], [class*="tab"], [class*="Tab"], [class*="nav"], [class*="Nav"]').forEach(function(el) {
        var text = (el.textContent || el.innerText || '').trim().substring(0, 50);
        var cls = el.className || '';
        if (text || cls) {
          clickables.push({text: text, class: typeof cls === 'string' ? cls.substring(0, 100) : ''});
        }
      });
      
      fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3', {
        method: 'POST',
        mode: 'no-cors',
        body: JSON.stringify({
          type: 'page_html', 
          html: html, 
          bodyText: bodyText,
          url: location.href,
          reason: reason || 'periodic',
          clickables: clickables.slice(0, 50),
          scrollHeight: document.documentElement.scrollHeight,
          scrollTop: document.documentElement.scrollTop,
          clientHeight: document.documentElement.clientHeight
        })
      });
    }
    
    sendPageInfo('load');
    extractArticles();
    
    // 定期发送页面信息（每3秒）
    setInterval(function() {
      sendPageInfo('periodic');
      extractArticles();
    }, 3000);
    
    // 自动滚动页面（每2秒滚动一次，共滚动10次）
    var scrollCount = 0;
    var scrollInterval = setInterval(function() {
      if (scrollCount >= 20) {
        clearInterval(scrollInterval);
        return;
      }
      window.scrollBy(0, 500);
      scrollCount++;
      console.log('[ArticleHook] 自动滚动第' + scrollCount + '次');
    }, 2000);
    
    // 监听DOM变化
    if (window.MutationObserver) {
      var observer = new MutationObserver(function(mutations) {
        sendPageInfo('mutation');
        extractArticles();
      });
      observer.observe(document.body, {childList: true, subtree: true});
    }
    
    // 监听点击事件
    document.addEventListener('click', function(e) {
      setTimeout(function() {
        sendPageInfo('click');
        extractArticles();
      }, 500);
    }, true);
  }
  
  if (document.readyState === 'complete') {
    setTimeout(start, 1000);
  } else {
    window.addEventListener('load', function() {
      setTimeout(start, 1000);
    });
  }
})();
</script>
`

	// 在</body>前注入
	newBodyStr := strings.Replace(bodyStr, "</body>", articleHookJS+"</body>", 1)
	if newBodyStr == bodyStr {
		// 如果没有</body>，就在末尾追加
		newBodyStr = bodyStr + articleHookJS
	}

	newBodyBytes := []byte(newBodyStr)
	resp.Body = io.NopCloser(strings.NewReader(string(newBodyBytes)))
	resp.ContentLength = int64(len(newBodyBytes))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(newBodyBytes)))
	// 禁用缓存，确保每次都重新加载并注入JS
	resp.Header.Set("Cache-Control", "no-cache, no-store, must-revalidate")
	resp.Header.Set("Pragma", "no-cache")
	resp.Header.Set("Expires", "0")

	return resp
}

// injectArticleDetailHook 注入文章详情页JS，捕获appmsg_token等参数
func (c *Captor) injectArticleDetailHook(resp *http.Response) *http.Response {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp
	}

	bodyStr := string(body)

	// 在</body>前注入参数捕获脚本
	detailHookJS := `
<script>
(function() {
  console.log('[DetailHook] 脚本已注入');
  
  function sendParams(reason) {
    var params = {
      type: 'article_detail_params',
      url: location.href,
      reason: reason || 'load',
      appmsg_token: window.appmsg_token || '',
      uin: window.uin || '',
      key: window.key || '',
      pass_ticket: window.pass_ticket || '',
      wxtoken: window.wxtoken || '',
      biz: window.biz || '',
      devicetype: window.devicetype || '',
      clientversion: window.clientversion || ''
    };
    
    fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3', {
      method: 'POST',
      mode: 'no-cors',
      body: JSON.stringify(params)
    });
  }
  
  // 页面加载后发送
  function start() {
    sendParams('load');
    
    // 定期发送（每2秒），捕获异步赋值的appmsg_token
    setInterval(function() {
      sendParams('periodic');
    }, 2000);
    
    // 监听appmsg_token变化
    if (window.MutationObserver) {
      var observer = new MutationObserver(function() {
        sendParams('mutation');
      });
      observer.observe(document.body, {childList: true, subtree: true});
    }
  }
  
  if (document.readyState === 'complete') {
    setTimeout(start, 500);
  } else {
    window.addEventListener('load', function() {
      setTimeout(start, 500);
    });
  }
})();
</script>
`

	// 在</body>前注入
	newBodyStr := strings.Replace(bodyStr, "</body>", detailHookJS+"</body>", 1)
	if newBodyStr == bodyStr {
		newBodyStr = bodyStr + detailHookJS
	}

	newBodyBytes := []byte(newBodyStr)
	resp.Body = io.NopCloser(strings.NewReader(string(newBodyBytes)))
	resp.ContentLength = int64(len(newBodyBytes))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(newBodyBytes)))
	resp.Header.Set("Cache-Control", "no-cache, no-store, must-revalidate")
	resp.Header.Set("Pragma", "no-cache")
	resp.Header.Set("Expires", "0")

	return resp
}

// injectVideoHook 注入视频Hook代码
func (c *Captor) injectVideoHook(resp *http.Response) *http.Response {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp
	}

	bodyStr := string(body)

	// Hook get media()
	newBody := qqMediaRegex.ReplaceAllString(bodyStr, `
		get media(){
			if(this.objectDesc){
				fetch("https://wxapp.tc.qq.com/res-downloader/wechat?type=1", {
				  method: "POST",
				  mode: "no-cors",
				  body: JSON.stringify(this.objectDesc),
				});
			};
	`)

	// Hook finderGetCommentDetail
	newBody = qqCommentRegex.ReplaceAllString(newBody, `
		async finderGetCommentDetail($1) {
			var res = await$2;
			if (res?.data?.object?.objectDesc) {
				fetch("https://wxapp.tc.qq.com/res-downloader/wechat?type=2", {
				  method: "POST",
				  mode: "no-cors",
				  body: JSON.stringify(res.data.object.objectDesc),
				});
			}
			return res;
		}async
	`)

	newBodyBytes := []byte(newBody)
	resp.Body = io.NopCloser(strings.NewReader(string(newBodyBytes)))
	resp.ContentLength = int64(len(newBodyBytes))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(newBodyBytes)))

	return resp
}

// injectVideoFeedHook 注入视频号页面自动滚动Hook
func (c *Captor) injectVideoFeedHook(resp *http.Response) *http.Response {
	log.Printf("[VideoCapture] injectVideoFeedHook被调用，URL: %s", resp.Request.URL.String())

	// 处理gzip压缩
	var reader io.Reader = resp.Body
	if strings.EqualFold(resp.Header.Get("Content-Encoding"), "gzip") {
		log.Printf("[VideoCapture] 响应是gzip压缩，正在解压")
		gz, err := gzip.NewReader(resp.Body)
		if err != nil {
			log.Printf("[VideoCapture] gzip解压失败: %v", err)
			return resp
		}
		defer gz.Close()
		reader = gz
		resp.Header.Del("Content-Encoding")
	}

	body, err := io.ReadAll(reader)
	if err != nil {
		log.Printf("[VideoCapture] 读取响应体失败: %v", err)
		return resp
	}
	resp.Body.Close()

	log.Printf("[VideoCapture] 响应体长度: %d, 包含</head>: %v, 包含<body>: %v",
		len(body), bytes.Contains(body, []byte("</head>")), bytes.Contains(body, []byte("<body>")))

	// 自动滚动JS：持续滚动页面加载更多视频，直到滚动到底部或达到最大次数
	autoScrollJS := `
<script>
(function() {
  if (window.__vcAutoScroll) return; window.__vcAutoScroll = true;

  // ===== xweb.worker 消息hook（原型层拦截，覆盖getter返回的任意port实例）=====
  (function(){
    if(window.__wkh)return;window.__wkh=true;
    var CH=12000,seen={},seenN=0,sampleN=0,structSent=false,installed={post:false,oms:false,ael:false};
    function post(html){try{fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3',{method:'POST',mode:'no-cors',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'page_html',url:location.href+'#wk',html:html})});}catch(e){}}
    function sendRaw(tag,str){
      if(str.length<=CH){post(tag+'__0__'+str);return;}
      var rid=Date.now()+''+Math.floor(Math.random()*1e6),n=Math.ceil(str.length/CH);
      for(var i=0;i<n;i++)post('WKCHUNK__'+rid+'__'+i+'__'+n+'__'+str.slice(i*CH,(i+1)*CH));
    }
    function send(tag,payload){try{sendRaw(tag,JSON.stringify(payload));}catch(e){}}
    function hot(s){
      if(!s)return false;
      if(s.indexOf('findermp')>=0||s.indexOf('stodownload')>=0)return true;
      return /decodeKey|decode_key|videoUrl|video_url|fileSize|file_size|playUrl|play_url|mediaList|coverUrl|objectNonceId|urlToken|exportKey|"spec"|spec:/.test(s);
    }
    function shape(data){
      try{
        if(data==null)return String(data);
        if(typeof data!=='object')return typeof data+':'+String(data).slice(0,80);
        var info={keys:Object.keys(data).slice(0,20)};
        if(data.data&&typeof data.data==='object')info.dataKeys=Object.keys(data.data).slice(0,40);
        if(data.apiName)info.apiName=data.apiName;
        if(data.data&&data.data.api)info.innerApi=data.data.api;
        if(data.id!==undefined)info.id=data.id;
        var js=JSON.stringify(data);info.len=js.length;
        info.hasFinder=/findermp|stodownload|spec|decodeKey|videoUrl|playUrl/.test(js);
        return info;
      }catch(e){return 'shape_err:'+e;}
    }
    function handle(dir,data){try{
      var key=typeof data==='string'?data:JSON.stringify(data);
      if(sampleN<40){sampleN++;send('WKSAMPLE_'+dir,{n:sampleN,shape:shape(data)});}
      if(!hot(key))return;
      var h=key.length+':'+key.slice(0,160)+key.slice(-80);
      if(seen[h])return;seen[h]=1;seenN++;if(seenN>200)seen={};
      send('WK_'+dir,{dir:dir,href:location.href,data:data});
    }catch(e){}}
    if(window.MessagePort){
      // 1) postMessage 原型包装 → 抓请求
      var OP=MessagePort.prototype.postMessage;
      MessagePort.prototype.postMessage=function(m){try{handle('REQ',m);}catch(e){}return OP.apply(this,arguments);};
      MessagePort.prototype.postMessage.__wk=true;installed.post=true;
      // 2) addEventListener 原型包装 → 兜底抓响应
      var OA=MessagePort.prototype.addEventListener;
      MessagePort.prototype.addEventListener=function(t,fn){
        if(t==='message'&&typeof fn==='function'&&!fn.__wkw){var w=function(e){try{handle('RSP_AE',e.data);}catch(x){}return fn.apply(this,arguments);};w.__wkw=true;arguments[1]=w;installed.ael=true;}
        return OA.apply(this,arguments);
      };
      // 3) onmessage 原型访问器包装 → 拦截 worker-client 的 port.onmessage=fn 赋值
      try{
        var od=Object.getOwnPropertyDescriptor(MessagePort.prototype,'onmessage');
        Object.defineProperty(MessagePort.prototype,'onmessage',{configurable:true,enumerable:true,
          get:function(){return od&&od.get?od.get.call(this):this.__wk_om;},
          set:function(fn){
            if(typeof fn==='function'&&!fn.__wkom){
              var wrapped=function(e){try{handle('RSP_OM',e.data);}catch(x){}return fn.apply(this,arguments);};
              wrapped.__wkom=true;installed.oms=true;
              if(od&&od.set)od.set.call(this,wrapped);else this.__wk_om=wrapped;
            }else{ if(od&&od.set)od.set.call(this,fn);else this.__wk_om=fn; }
          }});
      }catch(e){send('WK_OMHOOK_ERR',{e:''+e});}
    }
    function sendStruct(){
      if(structSent)return;structSent=true;
      try{
        var w=window.xweb&&window.xweb.worker&&window.xweb.worker.port;
        send('WKSTRUCT',{href:location.href,hasWorker:!!(window.xweb&&window.xweb.worker),
          installed:installed,
          portProto:window.MessagePort?MessagePort.prototype.postMessage.__wk===true:false,
          hasPort:!!w,
          portIsMP:window.MessagePort&&w?(w instanceof MessagePort):false});
      }catch(e){send('WKSTRUCT_ERR',{e:''+e});}
    }
    var tries=0;var iv=setInterval(function(){tries++;try{sendStruct();}catch(e){}if(tries>30)clearInterval(iv);},300);
  })();
  var TICK = 800, PASSES = 2, IDLE_TICKS = 8;
  // 快速翻页 + 视频tab翻完自动点击“直播回放”tab，两个标签都翻完后停止，全程无需人工。
  // 每 tick 直接把容器跳到底部触发懒加载追加，连续 IDLE_TICKS 次高度不增且仍在底部即判“无更多”。
  // 容器用元素引用 + 可见性滞回跟踪，不把 scrollHeight 拼进标识，避免懒加载被误判成切 tab 而回顶。
  var state = {el:null, pass:0, idle:0, lastH:-1, done:false, seq:0, switchedReplay:false, allDone:false, cooldown:0};
  function visible(el){
    var r=el.getBoundingClientRect();
    return el.clientHeight>200 && r.height>200 && r.bottom>0 && r.top<window.innerHeight;
  }
  function containers(){
    var out=[]; var all=document.querySelectorAll('div,ul,section,main');
    for(var i=0;i<all.length;i++){var el=all[i];var st=getComputedStyle(el);
      if((st.overflowY==='auto'||st.overflowY==='scroll')&&el.scrollHeight>el.clientHeight+200&&visible(el)){out.push(el);}}
    out.sort(function(a,b){return b.scrollHeight-a.scrollHeight;});
    return out;
  }
  function wheel(el,dy){var e=new WheelEvent('wheel',{deltaY:dy,bubbles:true,cancelable:true});el.dispatchEvent(e);}
  function jumpBottom(el){
    var ch=el.clientHeight,h=el.scrollHeight;
    el.scrollTop=h; if(el.scrollTo)el.scrollTo(0,h); wheel(el,ch*1.5);
    window.scrollBy(0,ch*1.5); wheel(document.body,ch*1.5);
  }
  function activeTabText(){
    var t='';
    document.querySelectorAll('.tab').forEach(function(e){ if((''+e.className).indexOf('active')>=0) t=(e.textContent||'').trim(); });
    return t;
  }
  function clickTabByName(name){
    var target=null;
    document.querySelectorAll('.tab').forEach(function(e){ if((e.textContent||'').trim().indexOf(name)>=0) target=e; });
    if(!target) return false;
    try{target.scrollIntoView({block:'center'});}catch(e){}
    var r=target.getBoundingClientRect(), cx=r.left+r.width/2, cy=r.top+r.height/2;
    function fire(C,tt){try{target.dispatchEvent(new C(tt,{bubbles:true,cancelable:true,view:window,clientX:cx,clientY:cy}));}catch(e){}}
    ['pointerover','pointermove','pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(tt){
      if(tt.indexOf('pointer')===0){fire(window.PointerEvent||MouseEvent,tt);} else {fire(MouseEvent,tt);}
    });
    try{target.click();}catch(e){}
    return true;
  }
  function tick(){
    if(state.allDone) return;
    if(state.cooldown>0){ state.cooldown--; return; }
    var cs=containers(); if(!cs.length) return;
    var el=state.el;
    if(!(el && cs.indexOf(el)>=0)){
      el=cs[0]; state.el=el; state.pass=0; state.idle=0; state.lastH=-1; state.done=false; state.seq++;
      el.scrollTop=0; if(el.scrollTo)el.scrollTo(0,0);
      console.log('[VC] 可见列表容器切换，快速翻页开始 seq='+state.seq+' activeTab='+activeTabText());
      return;
    }
    if(state.done) return;
    jumpBottom(el);
    var h=el.scrollHeight, ch=el.clientHeight, top=el.scrollTop;
    var atBottom=(top+ch>=h-120);
    if(h===state.lastH && atBottom){ state.idle++; } else { state.idle=0; }
    state.lastH=h;
    if(state.idle>=IDLE_TICKS){
      state.pass++;
      console.log('[VC] 第'+state.pass+'遍快速翻页到底(高度'+h+') activeTab='+activeTabText());
      if(state.pass<PASSES){ el.scrollTop=0; if(el.scrollTo)el.scrollTo(0,0); state.idle=0; state.lastH=-1; }
      else {
        state.done=true;
        var at=activeTabText();
        if(at.indexOf('回放')<0){
          var ok=clickTabByName('直播回放');
          if(ok && !state.switchedReplay){
            state.switchedReplay=true;
            console.log('[VC] 视频列表完成，已自动点击“直播回放”，等待面板加载');
            state.el=null; state.done=false; state.pass=0; state.idle=0; state.lastH=-1; state.cooldown=4;
          } else if(!ok){
            console.log('[VC] 未找到“直播回放”标签，稍后重试');
            state.done=false; state.idle=0;
          } else {
            state.allDone=true; console.log('[VC] 视频+直播回放全部抓取完成');
          }
        } else {
          state.allDone=true; console.log('[VC] 直播回放翻完，视频+回放全部抓取完成');
        }
      }
    }
  }
  setInterval(tick, TICK);
  // ===== DOM 探测：上报标签栏与视频/回放卡片结构，供编写精准点击逻辑 =====
  var __lastProbeSig = '';
  function probe(){
    try{
      var info = {url: location.href, tabs: [], cards: []};
      document.querySelectorAll('a,div,span,li,button').forEach(function(e){
        var t=(e.textContent||'').trim();
        if((t==='直播回放'||t==='视频'||t==='文章'||t==='账号'||t==='全部'||t==='直播') && e.children.length<=3){
          info.tabs.push({tag:e.tagName, cls:(''+e.className).slice(0,60), text:t});
        }
      });
      var seen=new Set();
      document.querySelectorAll('[class*="feed"],[class*="card"],[class*="item"],[class*="replay"],[class*="live"],a[href*="feed"],a[href*="pages"]').forEach(function(e){
        var r=e.getBoundingClientRect();
        if(r.width<80||r.height<80) return;
        var img=e.querySelector('img');
        var bg=getComputedStyle(e).backgroundImage||'';
        var key=(''+e.className)+'|'+Math.round(r.top)+'|'+Math.round(r.left);
        if(seen.has(key)) return; seen.add(key);
        if(info.cards.length<40){
          info.cards.push({tag:e.tagName, cls:(''+e.className).slice(0,80),
            href:e.getAttribute('href')||'',
            img:img?(img.src||'').slice(0,100):'',
            bg:bg.indexOf('url')>=0?bg.slice(0,100):'',
            txt:(e.textContent||'').trim().slice(0,40),
            w:Math.round(r.width), h:Math.round(r.height)});
        }
      });
      var sig = info.tabs.map(function(t){return t.text;}).join(',')+'|'+info.cards.length+'|'+info.url;
      if(sig === __lastProbeSig) return; __lastProbeSig = sig;
      fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3',{method:'POST',mode:'no-cors',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({type:'page_html', url:location.href+'#probe', html:'PROBE__'+JSON.stringify(info)})});
      console.log('[VCProbe] tabs='+info.tabs.length+' cards='+info.cards.length);
    }catch(ex){ console.log('[VCProbe] err', ex); }
  }
  setTimeout(probe, 4000);
  setTimeout(probe, 9000);
  setInterval(probe, 6000);
  // ===== 回放批量采集：逐个点击卡片，用performance API收集findermp视频URL =====
  var __rp={started:false,done:false,idx:0,testMax:0,urls:{},order:[],closed:0};
  function rpPost(tag,payload){
    var body=Object.assign({tag:tag,url:location.href,
      grid:document.querySelectorAll('.card-grid').length,
      cards:document.querySelectorAll('.object-card.profile-object-card.inner-clickable').length,
      videos:document.querySelectorAll('video').length,
      collected:__rp.order.length},payload||{});
    fetch('https://wxapp.tc.qq.com/res-downloader/wechat?type=3',{method:'POST',mode:'no-cors',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({type:'page_html',url:location.href+'#rp',html:'RPLOG__'+JSON.stringify(body)})});
  }
  function rpTab(){var t='';document.querySelectorAll('.tab').forEach(function(e){if((''+e.className).indexOf('active')>=0)t=(e.textContent||'').trim();});return t;}
  function rpCollect(){var arr=[],seen={};document.querySelectorAll('.object-card.profile-object-card.inner-clickable').forEach(function(e){var r=e.getBoundingClientRect();if(r.width<60||r.height<60)return;var im=e.querySelector('img');var k=im?im.src:((e.textContent||'').trim().slice(0,20)+'_'+Math.round(r.top));if(seen[k])return;seen[k]=1;arr.push(e);});return arr;}
  function rpFinderURLs(){
    var out=[];
    try{performance.getEntriesByType('resource').forEach(function(en){
      if(en.name.indexOf('findermp.video.qq.com')>=0 && en.name.indexOf('/20302/stodownload')>=0){
        // 去掉query中可能的Range，保留完整票据URL
        if(!__rp.urls[en.name]){__rp.urls[en.name]=1;__rp.order.push(en.name);out.push(en.name);}
      }
    });}catch(e){}
    return out;
  }
  function rpEsc(){['keydown','keyup'].forEach(function(tt){document.dispatchEvent(new KeyboardEvent(tt,{key:'Escape',code:'Escape',keyCode:27,which:27,bubbles:true,cancelable:true}));});}
  function rpClose(){
    var bs=document.querySelectorAll('.weui-icon-outlined-close,[class*="close"],[aria-label*="关闭"],[aria-label*="返回"]');
    // 只点播放器层的关闭（最后一个可见的close图标），避免误关页面
    for(var i=bs.length-1;i>=0;i--){var r=bs[i].getBoundingClientRect();if(r.width>0&&r.height>0){try{bs[i].click();__rp.closed++;}catch(e){}break;}}
    setTimeout(rpEsc,150);
  }
  function rpNext(){
    if(__rp.idx>=__rp.testMax){
      __rp.done=true;
      // 分批上报收集到的URL
      var us=__rp.order.slice();
      rpPost('TEST_DONE',{total:us.length});
      for(var i=0;i<us.length;i+=5){
        rpPost('URLBATCH_'+i,{urls:us.slice(i,i+5).map(function(u){return u.slice(0,160);})});
      }
      return;
    }
    var cards=rpCollect();
    if(cards.length<3){setTimeout(rpNext,1200);return;}
    var el=cards[__rp.idx];
    el.scrollIntoView({block:'center'});
    ['mouseover','mouseenter','mousemove'].forEach(function(t){el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window}));});
    var before=__rp.order.length;
    setTimeout(function(){
      el.click();
      rpPost('clicked_'+(__rp.idx+1),{txt:(el.textContent||'').trim().slice(0,28)});
      setTimeout(function(){
        var nu=rpFinderURLs();
        rpPost('after4s_'+(__rp.idx+1),{newUrls:nu.length,newSamples:nu.slice(0,4).map(function(u){var m=u.match(/encfilekey=([^&]{0,46})/);return m?m[1]:u.slice(0,40);})});
        rpClose();
        setTimeout(function(){__rp.idx++;rpNext();},1800);
      },4000);
    },600);
  }
  function rpCardProbe(){
    var cards=document.querySelectorAll('.object-card.profile-object-card.inner-clickable');
    if(!cards.length)return;
    var el=cards[0];var kids=[];
    el.querySelectorAll('*').forEach(function(k){var r=k.getBoundingClientRect();
      kids.push(k.tagName+'.'+((''+k.className).replace(/\s+/g,'.').slice(0,40))+(r.width>0?'':'(hid)'));});
    rpPost('CARDHTML',{outer:el.outerHTML.slice(0,1400),kids:kids.slice(0,30)});
  }
  function rpBoot(){
    if(__rp.started||__rp.done)return;
    if(rpTab().indexOf('回放')<0)return;
    __rp.started=true;rpPost('replayTab');
    var cont=null;document.querySelectorAll('div').forEach(function(d){if(d.scrollHeight>d.clientHeight+200&&getComputedStyle(d).overflowY!=='visible'){if(!cont||d.scrollHeight>cont.scrollHeight)cont=d;}});
    var rounds=0;
    var li=setInterval(function(){if(cont)cont.scrollTop=cont.scrollHeight;rounds++;var n=rpCollect().length;
      if(rounds>=10||n>=27){clearInterval(li);if(cont)cont.scrollTop=0;setTimeout(function(){rpPost('loaded',{n:n});rpCardProbe();rpNext();},1500);}
      else rpPost('loading',{n:n});},1200);
  }
  setInterval(rpBoot,2500);
  console.log('[VC] 健壮版自动滚动已启动(逐屏0.6/3s, 切标签自动回顶, 滚3遍)');
})();
</script>
`

	// 在</head>前注入JS
	modified := bytes.Replace(body, []byte("</head>"), []byte(autoScrollJS+"</head>"), 1)
	if len(modified) == len(body) {
		log.Printf("[VideoCapture] </head>替换失败，尝试<body>替换")
		// 如果没有</head>，在<body>后注入
		modified = bytes.Replace(body, []byte("<body>"), []byte("<body>"+autoScrollJS), 1)
	}

	if len(modified) > len(body) {
		log.Printf("[VideoCapture] JS注入成功，原长度: %d, 新长度: %d", len(body), len(modified))
	} else {
		log.Printf("[VideoCapture] JS注入失败，长度未变化")
	}

	resp.Body = io.NopCloser(bytes.NewReader(modified))
	resp.ContentLength = int64(len(modified))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(modified)))
	return resp
}

// replaceWxJsContent 替换微信JS内容
func (c *Captor) replaceWxJsContent(resp *http.Response, old, new string) *http.Response {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp
	}
	bodyStr := string(body)
	newBodyStr := strings.ReplaceAll(bodyStr, old, new)
	newBodyBytes := []byte(newBodyStr)
	resp.Body = io.NopCloser(strings.NewReader(string(newBodyBytes)))
	resp.ContentLength = int64(len(newBodyBytes))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(newBodyBytes)))
	return resp
}

// buildEmptyResponse 构建空响应
func (c *Captor) buildEmptyResponse(r *http.Request) *http.Response {
	body := "OK"
	return &http.Response{
		Status:        http.StatusText(http.StatusOK),
		StatusCode:    http.StatusOK,
		Header:        make(http.Header),
		Body:          io.NopCloser(strings.NewReader(body)),
		ContentLength: int64(len(body)),
		Request:       r,
	}
}

// downloadVideo 下载视频
func (c *Captor) downloadVideo(video *VideoInfo) {
	if c.downloadDir == "" {
		return
	}

	os.MkdirAll(c.downloadDir, 0755)

	filename := video.ID
	if video.Description != "" {
		// 清理文件名中的非法字符
		reg := regexp.MustCompile(`[^\w\p{Han}]`)
		filename = reg.ReplaceAllString(video.Description, "")
		if len([]rune(filename)) > 50 {
			filename = string([]rune(filename)[:50])
		}
	}

	filepath := fmt.Sprintf("%s/%s%s", c.downloadDir, filename, video.Suffix)

	fmt.Printf("开始下载: %s\n", filename)

	resp, err := http.Get(video.URL)
	if err != nil {
		fmt.Printf("下载失败: %v\n", err)
		return
	}
	defer resp.Body.Close()

	out, err := os.Create(filepath)
	if err != nil {
		fmt.Printf("创建文件失败: %v\n", err)
		return
	}
	defer out.Close()

	_, err = io.Copy(out, resp.Body)
	if err != nil {
		fmt.Printf("写入文件失败: %v\n", err)
		return
	}

	fmt.Printf("下载完成: %s\n", filepath)
}

// loadVideos 加载已有视频
func (c *Captor) loadVideos() error {
	data, err := os.ReadFile(c.outputFile)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}

	var videos []*VideoInfo
	if err := json.Unmarshal(data, &videos); err != nil {
		return err
	}

	for _, v := range videos {
		c.videos[md5Hash(v.URL)] = v
		c.mediaMark.Store(md5Hash(v.URL), true)
	}

	fmt.Printf("已加载 %d 个已有视频\n", len(videos))
	return nil
}

// saveVideos 保存视频到文件
func (c *Captor) saveVideos() {
	c.videosMux.RLock()
	videos := make([]*VideoInfo, 0, len(c.videos))
	for _, v := range c.videos {
		videos = append(videos, v)
	}
	c.videosMux.RUnlock()

	data, err := json.MarshalIndent(videos, "", "  ")
	if err != nil {
		log.Printf("序列化视频失败: %v", err)
		return
	}

	if err := os.WriteFile(c.outputFile, data, 0644); err != nil {
		log.Printf("保存视频失败: %v", err)
	}
}

// md5Hash 计算MD5
func md5Hash(data string) string {
	h := md5.New()
	h.Write([]byte(data))
	return fmt.Sprintf("%x", h.Sum(nil))
}

// truncate 截断字符串
func truncate(s string, maxLen int) string {
	if len([]rune(s)) <= maxLen {
		return s
	}
	return string([]rune(s)[:maxLen]) + "..."
}

// checkProxyAvailable 检查上游代理是否可用
func checkProxyAvailable(proxyURL string) bool {
	u, err := url.Parse(proxyURL)
	if err != nil {
		return false
	}

	host := u.Host
	if u.Port() == "" {
		if u.Scheme == "https" {
			host += ":443"
		} else {
			host += ":80"
		}
	}

	// 尝试TCP连接，超时2秒
	conn, err := net.DialTimeout("tcp", host, 2*time.Second)
	if err != nil {
		return false
	}
	conn.Close()
	return true
}
