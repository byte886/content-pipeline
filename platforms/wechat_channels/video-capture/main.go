package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
)

var (
	port          int
	outputFile    string
	autoDownload  bool
	downloadDir   string
	caCertPath    string
	caKeyPath     string
	noAutoProxy   bool
	upstreamProxy string
	autoScroll    bool
	replayList    bool
	shortProbe    bool
	mpRecon       bool
	passive       bool
)

func main() {
	flag.IntVar(&port, "port", 8899, "代理服务器端口")
	flag.StringVar(&outputFile, "output", "videos.json", "视频URL输出文件(JSON)")
	flag.BoolVar(&autoDownload, "download", false, "是否自动下载视频")
	flag.StringVar(&downloadDir, "download-dir", "./downloads", "视频下载目录")
	flag.StringVar(&caCertPath, "ca-cert", "", "CA证书路径(留空则自动生成)")
	flag.StringVar(&caKeyPath, "ca-key", "", "CA私钥路径(留空则自动生成)")
	flag.BoolVar(&noAutoProxy, "no-auto-proxy", false, "不自动设置系统代理(需手动配置)")
	flag.StringVar(&upstreamProxy, "upstream", "http://127.0.0.1:7890", "上游代理地址(默认ClashX，传空字符串禁用上游代理直连)")
	flag.BoolVar(&autoScroll, "autoscroll", false, "注入JS强制自动滚动视频号列表(默认关闭，由人工控制滚动)")
	flag.BoolVar(&replayList, "replay-list", false, "注入回放列表提取器:滚动加载全部回放卡片并从Vue组件提取oid/nid清单(不点击/不导航/不播放)")
	flag.BoolVar(&shortProbe, "short-probe", false, "注入短视频播放换签探针(静默不滚动/不点击;人工点开播放时抓带token签名直链)")
	flag.BoolVar(&mpRecon, "mp-recon", false, "公众号mp_profile只读侦察探针:枚举Vuex/Pinia、hook worker、定位文章数组与翻页action")
	flag.BoolVar(&passive, "passive", false, "纯被动记录:只全量落盘请求/响应,不注入JS、不自动翻页(用于定位真实接口)")
	flag.Parse()

	fmt.Println("========================================")
	fmt.Println("  视频号捕获工具 (命令行版 v2.0)")
	fmt.Println("========================================")
	fmt.Printf("代理端口: %d\n", port)
	fmt.Printf("输出文件: %s\n", outputFile)
	fmt.Printf("自动下载: %v\n", autoDownload)
	fmt.Printf("自动设置代理: %v\n", !noAutoProxy)
	fmt.Printf("强制自动滚动: %v\n", autoScroll)
	fmt.Printf("短视频播放探针: %v\n", shortProbe)
	if upstreamProxy != "" {
		fmt.Printf("上游代理: %s (ClashX规则路由)\n", upstreamProxy)
	} else {
		fmt.Printf("上游代理: 无 (直连)\n")
	}
	if autoDownload {
		fmt.Printf("下载目录: %s\n", downloadDir)
	}
	fmt.Println("========================================")

	// 自动设置系统代理
	if !noAutoProxy {
		fmt.Println("正在设置系统代理...")
		if err := setSystemProxy(port); err != nil {
			log.Printf("设置系统代理失败: %v", err)
			fmt.Println("请手动设置系统代理为 127.0.0.1:" + fmt.Sprintf("%d", port))
		}
		fmt.Println("========================================")
	}

	// 初始化捕获器
	captor, err := NewCaptor(port, outputFile, autoDownload, downloadDir, upstreamProxy, autoScroll, replayList, shortProbe, mpRecon, passive)
	if err != nil {
		// 退出前清除代理
		if !noAutoProxy {
			clearSystemProxy()
		}
		log.Fatalf("初始化失败: %v", err)
	}

	// 公众号历史页自动翻 getmsg 全量（独立 OnResponse handler）；passive 诊断模式不注册
	if !passive {
		captor.proxy.OnResponse().DoFunc(captor.articleExportHandler)
	}

	// 启动代理
	go func() {
		if err := captor.Start(); err != nil {
			log.Printf("代理启动失败: %v", err)
		}
	}()

	fmt.Println("代理服务器已启动，等待微信视频号流量...")
	fmt.Println("在微信中打开视频号，工具会自动捕获视频URL")
	fmt.Println("按 Ctrl+C 停止")
	fmt.Println("========================================")

	// 等待中断信号
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\n正在停止...")
	captor.Stop()

	// 清除系统代理
	if !noAutoProxy {
		fmt.Println("正在清除系统代理...")
		if err := clearSystemProxy(); err != nil {
			log.Printf("清除系统代理失败: %v", err)
		}
	}

	fmt.Println("已停止")
}
