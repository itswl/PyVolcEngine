package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strings"
	"time"
)

// APIConfig 存储API调用所需的配置信息
type APIConfig struct {
	AK         string
	SK         string
	Action     string
	Method     string
	Service    string
	Version    string
	Region     string
	Host       string
	ContentType string
	APIParams  map[string]interface{}
}

// APIError 自定义错误类型
type APIError struct {
	Message string
}

func (e *APIError) Error() string {
	return e.Message
}

// NewAPIConfig 从环境变量创建配置
func NewAPIConfig() (*APIConfig, error) {
	ak := os.Getenv("volcAK")
	if ak == "" {
		return nil, &APIError{Message: "访问密钥ID不能为空"}
	}

	sk := os.Getenv("volcSK")
	if sk == "" {
		return nil, &APIError{Message: "访问密钥不能为空"}
	}

	method := getEnvWithDefault("method", "GET")
	service := getEnvWithDefault("Service", "vpc")
	action := getEnvWithDefault("Action", "DescribeVpcs")
	version := getEnvWithDefault("Version", "2020-04-01")
	region := getEnvWithDefault("Region", "cn-shanghai")
	host := getEnvWithDefault("Host", "open.volcengineapi.com")
	contentType := getEnvWithDefault("ContentType", "application/json")

	apiParams, err := parseAPIParams()
	if err != nil {
		return nil, err
	}

	return &APIConfig{
		AK:         ak,
		SK:         sk,
		Action:     action,
		Method:     method,
		Service:    service,
		Version:    version,
		Region:     region,
		Host:       host,
		ContentType: contentType,
		APIParams:  apiParams,
	}, nil
}

// getEnvWithDefault 获取环境变量，如果不存在则返回默认值
func getEnvWithDefault(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// parseAPIParams 解析API参数
func parseAPIParams() (map[string]interface{}, error) {
	envParams := os.Getenv("API_PARAMS")
	if envParams == "" {
		return nil, nil
	}

	var params map[string]interface{}
	err := json.Unmarshal([]byte(envParams), &params)
	if err != nil {
		return nil, &APIError{Message: fmt.Sprintf("API参数解析失败: %v", err)}
	}

	return params, nil
}

// SignatureBuilder 签名构建器
type SignatureBuilder struct{}

// NormQuery 规范化查询参数
func (sb *SignatureBuilder) NormQuery(params map[string]interface{}) string {
	if len(params) == 0 {
		return ""
	}

	keys := make([]string, 0, len(params))
	for k := range params {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var queryItems []string
	for _, key := range keys {
		value := params[key]
		switch v := value.(type) {
		case []interface{}:
			for _, item := range v {
				queryItems = append(queryItems, fmt.Sprintf("%s=%s", 
					url.QueryEscape(key), 
					url.QueryEscape(fmt.Sprintf("%v", item))))
			}
		default:
			queryItems = append(queryItems, fmt.Sprintf("%s=%s", 
				url.QueryEscape(key), 
				url.QueryEscape(fmt.Sprintf("%v", value))))
		}
	}

	return strings.Replace(strings.Join(queryItems, "&"), "+", "%20", -1)
}

// HashSHA256 计算SHA256哈希
func (sb *SignatureBuilder) HashSHA256(content string) string {
	h := sha256.New()
	h.Write([]byte(content))
	return hex.EncodeToString(h.Sum(nil))
}

// HmacSHA256 计算HMAC-SHA256
func (sb *SignatureBuilder) HmacSHA256(key []byte, content string) []byte {
	h := hmac.New(sha256.New, key)
	h.Write([]byte(content))
	return h.Sum(nil)
}

// APIClient API客户端
type APIClient struct {
	Config          *APIConfig
	SignatureBuilder *SignatureBuilder
}

// NewAPIClient 创建API客户端
func NewAPIClient(config *APIConfig) *APIClient {
	return &APIClient{
		Config:          config,
		SignatureBuilder: &SignatureBuilder{},
	}
}

// SendRequest 发送API请求
func (client *APIClient) SendRequest() (map[string]interface{}, error) {
	now := time.Now().UTC()
	var body string
	if client.Config.APIParams != nil {
		bodyBytes, err := json.Marshal(client.Config.APIParams)
		if err != nil {
			return nil, &APIError{Message: fmt.Sprintf("序列化API参数失败: %v", err)}
		}
		body = string(bodyBytes)
	}

	requestParams := client.buildRequestParams(body, now)
	headers, err := client.buildHeaders(requestParams)
	if err != nil {
		return nil, err
	}

	response, err := client.makeRequest(requestParams, headers)
	if err != nil {
		return nil, err
	}

	return client.handleResponse(response)
}

// buildRequestParams 构建请求参数
func (client *APIClient) buildRequestParams(body string, date time.Time) map[string]interface{} {
	return map[string]interface{}{
		"body":        body,
		"host":        client.Config.Host,
		"path":        "/",
		"method":      client.Config.Method,
		"content_type": client.Config.ContentType,
		"date":        date,
		"query": map[string]interface{}{
			"Action":  client.Config.Action,
			"Version": client.Config.Version,
		},
	}
}

// buildHeaders 构建请求头
func (client *APIClient) buildHeaders(requestParams map[string]interface{}) (map[string]string, error) {
	date := requestParams["date"].(time.Time)
	xDate := date.Format("20060102T150405Z")
	shortDate := xDate[:8]
	body := requestParams["body"].(string)
	contentSha256 := client.SignatureBuilder.HashSHA256(body)

	headers := map[string]string{
		"Host":            requestParams["host"].(string),
		"X-Content-Sha256": contentSha256,
		"X-Date":          xDate,
		"Content-Type":    requestParams["content_type"].(string),
	}

	signature, err := client.calculateSignature(requestParams, xDate, shortDate, contentSha256)
	if err != nil {
		return nil, err
	}

	headers["Authorization"] = client.buildAuthorizationHeader(shortDate, signature)
	return headers, nil
}

// calculateSignature 计算签名
func (client *APIClient) calculateSignature(requestParams map[string]interface{}, xDate, shortDate, contentSha256 string) (string, error) {
	signedHeaders := []string{"content-type", "host", "x-content-sha256", "x-date"}
	signedHeadersStr := strings.Join(signedHeaders, ";")

	canonicalRequest, err := client.buildCanonicalRequest(requestParams, contentSha256, xDate, signedHeadersStr)
	if err != nil {
		return "", err
	}

	hashedCanonicalRequest := client.SignatureBuilder.HashSHA256(canonicalRequest)
	credentialScope := fmt.Sprintf("%s/%s/%s/request", shortDate, client.Config.Region, client.Config.Service)
	stringToSign := fmt.Sprintf("HMAC-SHA256\n%s\n%s\n%s", xDate, credentialScope, hashedCanonicalRequest)

	kDate := client.SignatureBuilder.HmacSHA256([]byte(client.Config.SK), shortDate)
	kRegion := client.SignatureBuilder.HmacSHA256(kDate, client.Config.Region)
	kService := client.SignatureBuilder.HmacSHA256(kRegion, client.Config.Service)
	kSigning := client.SignatureBuilder.HmacSHA256(kService, "request")

	signature := hex.EncodeToString(client.SignatureBuilder.HmacSHA256(kSigning, stringToSign))
	return signature, nil
}

// buildCanonicalRequest 构建规范请求
func (client *APIClient) buildCanonicalRequest(requestParams map[string]interface{}, contentSha256, xDate, signedHeadersStr string) (string, error) {
	query := requestParams["query"].(map[string]interface{})
	normQuery := client.SignatureBuilder.NormQuery(query)

	canonicalHeaders := []string{
		fmt.Sprintf("content-type:%s", requestParams["content_type"].(string)),
		fmt.Sprintf("host:%s", requestParams["host"].(string)),
		fmt.Sprintf("x-content-sha256:%s", contentSha256),
		fmt.Sprintf("x-date:%s", xDate),
	}

	canonicalRequest := strings.Join([]string{
		strings.ToUpper(requestParams["method"].(string)),
		requestParams["path"].(string),
		normQuery,
		strings.Join(canonicalHeaders, "\n"),
		"",
		signedHeadersStr,
		contentSha256,
	}, "\n")

	return canonicalRequest, nil
}

// buildAuthorizationHeader 构建授权头
func (client *APIClient) buildAuthorizationHeader(shortDate, signature string) string {
	credentialScope := fmt.Sprintf("%s/%s/%s/request", shortDate, client.Config.Region, client.Config.Service)
	return fmt.Sprintf("HMAC-SHA256 Credential=%s/%s, SignedHeaders=content-type;host;x-content-sha256;x-date, Signature=%s",
		client.Config.AK, credentialScope, signature)
}

// makeRequest 发送HTTP请求
func (client *APIClient) makeRequest(requestParams map[string]interface{}, headers map[string]string) (*http.Response, error) {
	query := requestParams["query"].(map[string]interface{})
	normQuery := client.SignatureBuilder.NormQuery(query)
	url := fmt.Sprintf("https://%s%s?%s", 
		requestParams["host"].(string), 
		requestParams["path"].(string), 
		normQuery)

	req, err := http.NewRequest(
		strings.ToUpper(requestParams["method"].(string)),
		url,
		bytes.NewBufferString(requestParams["body"].(string)),
	)
	if err != nil {
		return nil, &APIError{Message: fmt.Sprintf("创建HTTP请求失败: %v", err)}
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	// 将变量名从 client 改为 httpClient 以避免与接收者变量冲突
	httpClient := &http.Client{}
	return httpClient.Do(req)
}

// handleResponse 处理HTTP响应
func (client *APIClient) handleResponse(response *http.Response) (map[string]interface{}, error) {
	defer response.Body.Close()

	if response.StatusCode != 200 {
		bodyBytes, _ := io.ReadAll(response.Body)
		return nil, &APIError{Message: fmt.Sprintf("HTTP请求失败，状态码：%d\n响应内容：%s", 
			response.StatusCode, string(bodyBytes))}
	}

	bodyBytes, err := io.ReadAll(response.Body)
	if err != nil {
		return nil, &APIError{Message: fmt.Sprintf("读取响应内容失败: %v", err)}
	}

	if len(bodyBytes) == 0 {
		fmt.Println("任务执行成功，响应为空")
		return map[string]interface{}{}, nil
	}

	var result map[string]interface{}
	if err := json.Unmarshal(bodyBytes, &result); err != nil {
		return nil, &APIError{Message: fmt.Sprintf("响应内容不是有效的JSON格式：%s", string(bodyBytes))}
	}

	if metadata, ok := result["ResponseMetadata"].(map[string]interface{}); ok {
		if err, ok := metadata["Error"]; ok {
			return nil, &APIError{Message: fmt.Sprintf("任务执行失败：%v", err)}
		}
	}

	fmt.Println("任务执行成功")
	return result, nil
}

func main() {
	config, err := NewAPIConfig()
	if err != nil {
		fmt.Printf("错误：%s\n", err.Error())
		os.Exit(1)
	}

	client := NewAPIClient(config)
	response, err := client.SendRequest()
	if err != nil {
		fmt.Printf("错误：%s\n", err.Error())
		os.Exit(1)
	}

	jsonResponse, _ := json.MarshalIndent(response, "", "  ")
	fmt.Println(string(jsonResponse))
}