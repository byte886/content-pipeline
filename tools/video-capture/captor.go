package main

import (
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
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/elazarl/goproxy"
)

// VideoInfo 视频信息
type VideoInfo struct {
	ID          string            `json:"id"`
	URL         string            `json:"url"`
	CoverURL    string            `json:"cover_url"`
	Size        int64             `json:"size"`
	Description string            `json:"description"`
	Classify    string            `json:"classify"`
	Suffix      string            `json:"suffix"`
	DecodeKey   string            `json:"decode_key"`
	OtherData   map[string]string `json:"other_data"`
	CapturedAt  string            `json:"captured_at"`
}

// Captor 视频捕获器
type Captor struct {
	port         int
	outputFile   string
	autoDownload bool
	downloadDir  string
	proxy        *goproxy.ProxyHttpServer
	server       *http.Server
	videos       map[string]*VideoInfo
	videosMux    sync.RWMutex
	mediaMark    sync.Map
	version      string
}

var (
	qqMediaRegex   = regexp.MustCompile(`get\s*media\(\)\{`)
	qqCommentRegex = regexp.MustCompile(`async\s*finderGetCommentDetail\((\w+)\)\s*\{return(.*?)\s*}\s*async`)
)

// NewCaptor 创建捕获器
func NewCaptor(port int, outputFile string, autoDownload bool, downloadDir string) (*Captor, error) {
	c := &Captor{
		port:         port,
		outputFile:   outputFile,
		autoDownload: autoDownload,
		downloadDir:  downloadDir,
		videos:       make(map[string]*VideoInfo),
		version:      "1.0.0",
	}

	// 加载已有视频
	if err := c.loadVideos(); err != nil {
		log.Printf("加载已有视频失败: %v", err)
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
func (c *Captor) loadOrGenerateCA() (*tls.Certificate, error) {
	// 尝试加载已有证书
	if _, err := os.Stat("ca.crt"); err == nil {
		if _, err := os.Stat("ca.key"); err == nil {
			certPEM, err1 := os.ReadFile("ca.crt")
			keyPEM, err2 := os.ReadFile("ca.key")
			if err1 == nil && err2 == nil {
				cert, err := tls.X509KeyPair(certPEM, keyPEM)
				if err == nil {
					if cert.Leaf, err = x509.ParseCertificate(cert.Certificate[0]); err == nil {
						fmt.Println("已加载已有CA证书: ca.crt, ca.key")
						return &cert, nil
					}
				}
			}
		}
	}
	// 不存在或加载失败，生成新证书
	return c.generateCA()
}

// generateCA 生成自签名CA证书
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

	// 保存CA证书到文件
	os.WriteFile("ca.crt", certPEM, 0644)
	os.WriteFile("ca.key", keyPEM, 0600)
	fmt.Println("CA证书已生成: ca.crt, ca.key")
	fmt.Println("请在系统钥匙串中信任 ca.crt 证书")

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
	c.saveVideos()
}

// onRequest 请求处理
func (c *Captor) onRequest(r *http.Request, ctx *goproxy.ProxyCtx) (*http.Request, *http.Response) {
	// 处理微信视频号的回调请求
	if strings.Contains(r.Host, "qq.com") && strings.Contains(r.URL.Path, "/res-downloader/wechat") {
		return c.handleWechatRequest(r)
	}
	return r, nil
}

// onResponse 响应处理
func (c *Captor) onResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	if resp == nil || resp.Request == nil {
		return resp
	}

	host := resp.Request.Host
	path := resp.Request.URL.Path

	// 视频号页面 - 注入JS
	if strings.HasSuffix(host, "channels.weixin.qq.com") &&
		(strings.Contains(path, "/web/pages/feed") || strings.Contains(path, "/web/pages/home")) {
		return c.replaceWxJsContent(resp, ".js\"", fmt.Sprintf(".js?v=%s\"", c.version))
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

// handleWechatRequest 处理微信视频号的回调
func (c *Captor) handleWechatRequest(r *http.Request) (*http.Request, *http.Response) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return r, c.buildEmptyResponse(r)
	}

	go c.handleMedia(body)

	return r, c.buildEmptyResponse(r)
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

	urlSign := md5Hash(rawURL)
	if _, loaded := c.mediaMark.Load(urlSign); loaded {
		return
	}

	// 构建视频信息
	video := &VideoInfo{
		ID:          urlSign[:16],
		URL:         rawURL,
		Classify:    "video",
		Suffix:      ".mp4",
		OtherData:   make(map[string]string),
		CapturedAt:  time.Now().Format("2006-01-02 15:04:05"),
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

	// 文件大小
	switch size := firstMedia["fileSize"].(type) {
	case float64:
		video.Size = int64(size)
	case string:
		fmt.Sscanf(size, "%d", &video.Size)
	}

	// 封面URL
	if coverURL, ok := firstMedia["coverUrl"].(string); ok {
		video.CoverURL = coverURL
	}

	// 解密密钥
	if decodeKey, ok := firstMedia["decodeKey"].(string); ok {
		video.DecodeKey = decodeKey
	}

	// 描述
	if desc, ok := result["description"].(string); ok {
		video.Description = desc
	}

	// 视频格式
	if spec, ok := firstMedia["spec"].([]interface{}); ok {
		var formats []string
		for _, item := range spec {
			if m, ok := item.(map[string]interface{}); ok {
				if format, ok := m["fileFormat"].(string); ok {
					formats = append(formats, format)
				}
			}
		}
		video.OtherData["wx_file_formats"] = strings.Join(formats, "#")
	}

	c.mediaMark.Store(urlSign, true)

	// 保存视频
	c.videosMux.Lock()
	c.videos[urlSign] = video
	count := len(c.videos)
	c.videosMux.Unlock()

	// 立即保存到文件
	c.saveVideos()

	fmt.Printf("[%s] 捕获到新%s: %s\n", time.Now().Format("15:04:05"), video.Classify, truncate(video.Description, 50))
	if video.Description == "" {
		fmt.Printf("  URL: %s\n", truncate(video.URL, 80))
	}
	fmt.Printf("  总计: %d 个资源\n", count)

	// 自动下载
	if c.autoDownload && video.Classify == "video" {
		go c.downloadVideo(video)
	}
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
