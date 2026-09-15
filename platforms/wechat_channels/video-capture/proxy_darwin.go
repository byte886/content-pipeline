//go:build darwin

package main

import (
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

// getActiveNetworkServices 获取所有活动网络服务（有IP地址的）
func getActiveNetworkServices() ([]string, error) {
	output, err := exec.Command("networksetup", "-listallnetworkservices").CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("获取网络服务列表失败: %v", err)
	}

	services := strings.Split(string(output), "\n")
	var activeServices []string
	for _, service := range services {
		service = strings.TrimSpace(service)
		if service == "" || strings.Contains(service, "*") || strings.Contains(service, "Serial Port") {
			continue
		}

		// 检查是否有IP地址（活动状态）
		infoOutput, err := exec.Command("networksetup", "-getinfo", service).CombinedOutput()
		if err != nil {
			continue
		}
		if strings.Contains(string(infoOutput), "IP address:") {
			activeServices = append(activeServices, service)
		}
	}

	if len(activeServices) == 0 {
		return nil, fmt.Errorf("未找到活动网络服务")
	}

	return activeServices, nil
}

// setSystemProxy 设置系统代理（对所有活动网络服务）
func setSystemProxy(port int) error {
	services, err := getActiveNetworkServices()
	if err != nil {
		return err
	}

	portStr := fmt.Sprintf("%d", port)
	successCount := 0
	var errs []string

	for _, serviceName := range services {
		// 设置HTTP代理
		cmd1 := exec.Command("networksetup", "-setwebproxy", serviceName, "127.0.0.1", portStr)
		if output, err := cmd1.CombinedOutput(); err != nil {
			errs = append(errs, fmt.Sprintf("%s HTTP代理设置失败: %s", serviceName, output))
		} else {
			successCount++
		}

		// 设置HTTPS代理
		cmd2 := exec.Command("networksetup", "-setsecurewebproxy", serviceName, "127.0.0.1", portStr)
		if output, err := cmd2.CombinedOutput(); err != nil {
			errs = append(errs, fmt.Sprintf("%s HTTPS代理设置失败: %s", serviceName, output))
		} else {
			successCount++
		}
	}

	if successCount > 0 {
		fmt.Printf("已设置系统代理 (127.0.0.1:%d)，覆盖 %d 个网络服务\n", port, len(services))
		for _, s := range services {
			fmt.Printf("  - %s\n", s)
		}
		return nil
	}

	return fmt.Errorf("设置代理失败: %s", strings.Join(errs, "; "))
}

// clearSystemProxy 清除系统代理（对所有活动网络服务）
func clearSystemProxy() error {
	services, err := getActiveNetworkServices()
	if err != nil {
		return err
	}

	successCount := 0
	var errs []string

	for _, serviceName := range services {
		// 关闭HTTP代理
		cmd1 := exec.Command("networksetup", "-setwebproxystate", serviceName, "off")
		if output, err := cmd1.CombinedOutput(); err != nil {
			errs = append(errs, fmt.Sprintf("%s HTTP代理关闭失败: %s", serviceName, output))
		} else {
			successCount++
		}

		// 关闭HTTPS代理
		cmd2 := exec.Command("networksetup", "-setsecurewebproxystate", serviceName, "off")
		if output, err := cmd2.CombinedOutput(); err != nil {
			errs = append(errs, fmt.Sprintf("%s HTTPS代理关闭失败: %s", serviceName, output))
		} else {
			successCount++
		}
	}

	if successCount > 0 {
		fmt.Printf("已清除系统代理，覆盖 %d 个网络服务\n", len(services))
		return nil
	}

	return fmt.Errorf("清除代理失败: %s", strings.Join(errs, "; "))
}

// runWithSudo 使用sudo执行命令（需要密码）
func runWithSudo(password string, args ...string) ([]byte, error) {
	cmd := exec.Command("sudo", append([]string{"-S"}, args...)...)
	cmd.Stdin = bytes.NewReader([]byte(password + "\n"))
	return cmd.CombinedOutput()
}
