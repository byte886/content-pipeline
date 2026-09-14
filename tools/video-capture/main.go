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
	port         int
	outputFile   string
	autoDownload bool
	downloadDir  string
	caCertPath   string
	caKeyPath    string
	noAutoProxy  bool
)

func main() {
	flag.IntVar(&port, "port", 8899, "代理服务器端口")
	flag.StringVar(&outputFile, "output", "videos.json", "视频URL输出文件(JSON)")
	flag.BoolVar(&autoDownload, "download", false, "是否自动下载视频")
	flag.StringVar(&downloadDir, "download-dir", "./downloads", "视频下载目录")
	flag.StringVar(&caCertPath, "ca-cert", "", "CA证书路径(留空则自动生成)")
	flag.StringVar(&caKeyPath, "ca-key", "", "CA私钥路径(留空则自动生成)")
	flag.BoolVar(&noAutoProxy, "no-auto-proxy", false, "不自动设置系统代理(需手动配置)")
	flag.Parse()

	fmt.Println("========================================")
	fmt.Println("  视频号捕获工具 (命令行版 v2.0)")
	fmt.Println("========================================")
	fmt.Printf("代理端口: %d\n", port)
	fmt.Printf("输出文件: %s\n", outputFile)
	fmt.Printf("自动下载: %v\n", autoDownload)
	fmt.Printf("自动设置代理: %v\n", !noAutoProxy)
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
	captor, err := NewCaptor(port, outputFile, autoDownload, downloadDir)
	if err != nil {
		// 退出前清除代理
		if !noAutoProxy {
			clearSystemProxy()
		}
		log.Fatalf("初始化失败: %v", err)
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
