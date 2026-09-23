//go:build darwin

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// proxyState 单个协议（HTTP/HTTPS）的代理状态快照
type proxyState struct {
	Enabled bool   `json:"enabled"`
	Server  string `json:"server"`
	Port    string `json:"port"`
}

// proxySnapshot 物理服务在探针启动前的代理状态
type proxySnapshot struct {
	Service string     `json:"service"`
	HTTP    proxyState `json:"http"`
	HTTPS   proxyState `json:"https"`
}

func runCmd(name string, args ...string) (string, error) {
	out, err := exec.Command(name, args...).CombinedOutput()
	return string(out), err
}

// defaultPhysicalDevice 返回默认路由使用的接口（如 en0）
func defaultPhysicalDevice() (string, error) {
	out, err := runCmd("route", "-n", "get", "default")
	if err != nil {
		return "", fmt.Errorf("获取默认路由失败: %v", err)
	}
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "interface:") {
			return strings.TrimSpace(strings.TrimPrefix(line, "interface:")), nil
		}
	}
	return "", fmt.Errorf("默认路由中未找到 interface")
}

// physicalServiceForDevice 返回物理接口对应的网络服务名（如 en0 -> Ethernet）。
// 仅认可 hardware ports 中带真实 MAC 地址的端口，
// 从而排除 Tailscale 等 NetworkExtension/utun 虚拟服务。
func physicalServiceForDevice(device string) (string, error) {
	out, err := runCmd("networksetup", "-listallhardwareports")
	if err != nil {
		return "", err
	}
	for _, block := range strings.Split(out, "\n\n") {
		var hwPort, dev, mac string
		for _, line := range strings.Split(block, "\n") {
			line = strings.TrimSpace(line)
			switch {
			case strings.HasPrefix(line, "Hardware Port:"):
				hwPort = strings.TrimSpace(strings.TrimPrefix(line, "Hardware Port:"))
			case strings.HasPrefix(line, "Device:"):
				dev = strings.TrimSpace(strings.TrimPrefix(line, "Device:"))
			case strings.HasPrefix(line, "Ethernet Address:"):
				mac = strings.TrimSpace(strings.TrimPrefix(line, "Ethernet Address:"))
			}
		}
		if dev == device && hwPort != "" && mac != "" && mac != "N/A" {
			return hwPort, nil
		}
	}
	return "", fmt.Errorf("接口 %s 未匹配到物理网络服务（可能是 VPN/虚拟接口）", device)
}

func parseProxyState(out string) proxyState {
	ps := proxyState{}
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		switch {
		case strings.HasPrefix(line, "Enabled:"):
			ps.Enabled = strings.Contains(strings.TrimSpace(strings.TrimPrefix(line, "Enabled:")), "Yes")
		case strings.HasPrefix(line, "Server:"):
			ps.Server = strings.TrimSpace(strings.TrimPrefix(line, "Server:"))
		case strings.HasPrefix(line, "Port:"):
			ps.Port = strings.TrimSpace(strings.TrimPrefix(line, "Port:"))
		}
	}
	return ps
}

func snapshotPath(port int) string {
	return filepath.Join(os.TempDir(), fmt.Sprintf("captor_proxy_restore_%d.json", port))
}

// setSystemProxy 仅对默认路由对应的物理网络服务设置代理，
// 显式排除 Tailscale 等虚拟服务；设置前快照原代理，供停止时恢复。
func setSystemProxy(port int) error {
	device, err := defaultPhysicalDevice()
	if err != nil {
		return err
	}
	service, err := physicalServiceForDevice(device)
	if err != nil {
		return err
	}

	httpOut, _ := runCmd("networksetup", "-getwebproxy", service)
	httpsOut, _ := runCmd("networksetup", "-getsecurewebproxy", service)
	snap := proxySnapshot{
		Service: service,
		HTTP:    parseProxyState(httpOut),
		HTTPS:   parseProxyState(httpsOut),
	}
	data, _ := json.MarshalIndent(snap, "", "  ")
	if err := os.WriteFile(snapshotPath(port), data, 0600); err != nil {
		return fmt.Errorf("写入代理快照失败: %v", err)
	}

	portStr := fmt.Sprintf("%d", port)
	if _, err := runCmd("networksetup", "-setwebproxy", service, "127.0.0.1", portStr); err != nil {
		return fmt.Errorf("设置 HTTP 代理失败: %v", err)
	}
	if _, err := runCmd("networksetup", "-setsecurewebproxy", service, "127.0.0.1", portStr); err != nil {
		return fmt.Errorf("设置 HTTPS 代理失败: %v", err)
	}

	fmt.Printf("已设置系统代理 (127.0.0.1:%d)，物理服务=%s（已快照原设置；Tailscale 等虚拟服务已排除）\n", port, service)
	return nil
}

// restoreOne 将单个协议代理恢复到快照状态
func restoreOne(kind, service string, st proxyState) error {
	if st.Enabled && st.Server != "" && st.Port != "" {
		if kind == "http" {
			_, err := runCmd("networksetup", "-setwebproxy", service, st.Server, st.Port)
			return err
		}
		_, err := runCmd("networksetup", "-setsecurewebproxy", service, st.Server, st.Port)
		return err
	}
	if kind == "http" {
		_, err := runCmd("networksetup", "-setwebproxystate", service, "off")
		return err
	}
	_, err := runCmd("networksetup", "-setsecurewebproxystate", service, "off")
	return err
}

// clearSystemProxy 将物理服务代理恢复到探针启动前的快照状态；
// 无快照时兜底关闭物理服务代理。绝不触碰 Tailscale 等虚拟服务。
func clearSystemProxy() error {
	matches, _ := filepath.Glob(filepath.Join(os.TempDir(), "captor_proxy_restore_*.json"))

	if len(matches) == 0 {
		device, err := defaultPhysicalDevice()
		if err != nil {
			return err
		}
		service, err := physicalServiceForDevice(device)
		if err != nil {
			return err
		}
		_, e1 := runCmd("networksetup", "-setwebproxystate", service, "off")
		_, e2 := runCmd("networksetup", "-setsecurewebproxystate", service, "off")
		if e1 != nil || e2 != nil {
			return fmt.Errorf("兜底关闭代理失败: %v %v", e1, e2)
		}
		fmt.Printf("无快照，已关闭物理服务 %s 的代理\n", service)
		return nil
	}

	for _, path := range matches {
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		var snap proxySnapshot
		if err := json.Unmarshal(data, &snap); err != nil {
			continue
		}
		var errs []string
		if err := restoreOne("http", snap.Service, snap.HTTP); err != nil {
			errs = append(errs, "HTTP: "+err.Error())
		}
		if err := restoreOne("https", snap.Service, snap.HTTPS); err != nil {
			errs = append(errs, "HTTPS: "+err.Error())
		}
		os.Remove(path)
		if len(errs) > 0 {
			return fmt.Errorf("恢复 %s 代理失败: %s", snap.Service, strings.Join(errs, "; "))
		}
		fmt.Printf("已恢复物理服务 %s 代理到探针启动前状态（HTTP %s:%s enabled=%v；HTTPS %s:%s enabled=%v）\n",
			snap.Service, snap.HTTP.Server, snap.HTTP.Port, snap.HTTP.Enabled,
			snap.HTTPS.Server, snap.HTTPS.Port, snap.HTTPS.Enabled)
	}
	return nil
}
