API信息（兼容 易支付 接口）
接口地址：https://zpayz.cn/

商户ID（PID）：2025040215385823

商户密钥（PKEY）：Ltb8ZL7kuFg7ZgtnIbuIpJ350FoTXdqu

页面跳转支付
请求URL
https://zpayz.cn/submit.php
请求方法
POST 或 GET（推荐POST，不容易被劫持或屏蔽）
此接口可用于用户前台直接发起支付，使用form表单跳转或拼接成url跳转。
请求参数
参数	名称	类型	是否必填	描述	范例
name	商品名称	String	是	商品名称不超过100字	iphonexs max
money	订单金额	String	是	最多保留两位小数	5.67
type	支付方式	String	是	支付宝：alipay 微信支付：wxpay	alipay
out_trade_no	订单编号	Num	是	每个商品不可重复	201911914837526544601
notify_url	异步通知页面	String	是	交易信息回调页面，不支持带参数	http://www.aaa.com/bbb.php
pid	商户唯一标识	String	是	一串字母数字组合	201901151314084206659771
cid	支付渠道ID	String	否	如果不填则随机使用某一支付渠道	1234
param	附加内容	String	否	会通过notify_url原样返回	金色 256G
return_url	跳转页面	String	是	交易完成后浏览器跳转，不支持带参数	http://www.aaa.com/ccc.php
sign	签名（参考本页签名算法）	String	是	用于验证信息正确性，采用md5加密	28f9583617d9caf66834292b6ab1cc89
sign_type	签名方法	String	是	默认为MD5	MD5
用法举例
https://zpayz.cn/submit.php?name=iphone xs Max 一台&money=0.03&out_trade_no=201911914837526544601&notify_url=http://www.aaa.com/notify_url.php&pid=201901151314084206659771&param=金色 256G&return_url=http://www.baidu.com&sign=28f9583617d9caf66834292b6ab1cc89&sign_type=MD5&type=alipay

成功返回
直接跳转到付款页面
说明：该页面为收银台，直接访问这个url即可进行付款
失败返回
{"code":"error","msg":"具体的错误信息"}
API接口支付
请求URL
https://zpayz.cn/mapi.php
请求方法
POST（方式为form-data）
请求参数
字段名	变量名	必填	类型	示例值	描述
商户ID	pid	是	String	1001	
支付渠道ID	cid	否	String	1234	如果不填则随机使用某一支付渠道
支付方式	type	是	String	alipay	支付宝：alipay 微信支付：wxpay
商户订单号	out_trade_no	是	String	20160806151343349	
异步通知地址	notify_url	是	String	http://www.pay.com/notify_url.php	服务器异步通知地址
商品名称	name	是	String	VIP会员	如超过127个字节会自动截取
商品金额	money	是	String	1.00	单位：元，最大2位小数
用户IP地址	clientip	是	String	192.168.1.100	用户发起支付的IP地址
设备类型	device	否	String	pc	根据当前用户浏览器的UA判断，
传入用户所使用的浏览器
或设备类型，默认为pc
业务扩展参数	param	否	String	没有请留空	支付后原样返回
签名字符串	sign	是	String	202cb962ac59075b964b07152d234b70	签名算法参考本页底部
签名类型	sign_type	是	String	MD5	默认为MD5
成功返回
字段名	变量名	类型	示例值	描述
返回状态码	code	Int	1	1为成功，其它值为失败
返回信息	msg	String		失败时返回原因
订单号	trade_no	String	20160806151343349	支付订单号
ZPAY内部订单号	O_id	String	123456	ZPAY内部订单号
支付跳转url	payurl	String	https://xxx.cn/pay/wxpay/202010903/	如果返回该字段，则直接跳转到该url支付
二维码链接	qrcode	String	https://xxx.cn/pay/wxpay/202010903/	如果返回该字段，则根据该url生成二维码
二维码图片	img	String	https://zpayz.cn/qrcode/123.jpg	该字段为付款二维码的图片地址
失败返回
{"code":"error","msg":"具体的错误信息"}
查询单个订单
请求URL
https://zpayz.cn/api.php?act=order&pid={商户ID}&key={商户密钥}&out_trade_no={商户订单号}
请求方法
GET
请求参数
参数	名称	类型	必填	描述	范例
act	操作类型	String	是	此API固定值	order
pid	商户ID	String	是		20220715225121
key	商户密钥	String	是		89unJUB8HZ54Hj7x4nUj56HN4nUzUJ8i
trade_no	系统订单号	String	选择		20160806151343312
out_trade_no	商户订单号	String	选择		20160806151343349
返回结果
字段名	变量名	类型	示例值	描述
返回状态码	code	Int	1	1为成功，其它值为失败
返回信息	msg	String	查询订单号成功！	
易支付订单号	trade_no	String	2016080622555342651	易支付订单号
商户订单号	out_trade_no	String	20160806151343349	商户系统内部的订单号
支付方式	type	String	alipay	支付宝：alipay 微信支付：wxpay
商户ID	pid	String	20220715225121	发起支付的商户ID
创建订单时间	addtime	String	2016-08-06 22:55:52	
完成交易时间	endtime	String	2016-08-06 22:55:52	
商品名称	name	String	VIP会员	
商品金额	money	String	1.00	
支付状态	status	Int	0	1为支付成功，0为未支付
业务扩展参数	param	String		默认留空
支付者账号	buyer	String		默认留空
提交订单退款
请求URL
https://zpayz.cn/api.php?act=refund
请求方法
POST
请求参数
字段名	变量名	必填	类型	示例值	描述
商户ID	pid	是	String	20220715225121	
商户密钥	key	是	String	89unJUB8HZ54Hj7x4nUj56HN4nUzUJ8i	
易支付订单号	trade_no	特殊可选	String	20160806151343349021	易支付订单号
商户订单号	out_trade_no	特殊可选	String	20160806151343349	订单支付时传入的商户订单号，商家自定义且保证商家系统中唯一
退款金额	money	是	String	1.50	大多数通道需要与原订单金额一致
返回结果
字段名	变量名	类型	示例值	描述
返回状态码	code	Int	1	1为成功，其它值为失败
返回信息	msg	String	退款成功	
支付结果通知
请求URL
服务器异步通知（notify_url）、页面跳转通知（return_url）
请求方法
GET
请求参数
参数	名称	类型	描述	范例
pid	商户ID	Int		201901151314084206659771
name	商品名称	String	商品名称不超过100字	iphone
money	订单金额	String	最多保留两位小数	5.67
out_trade_no	商户订单号	Num	商户系统内部的订单号	201901191324552185692680
trade_no	易支付订单号	String	易支付订单号	2019011922001418111011411195
param	业务扩展参数	String	会通过notify_url原样返回	金色 256G
trade_status	支付状态	String	只有TRADE_SUCCESS是成功	TRADE_SUCCESS
type	支付方式	String	包括支付宝、微信	alipay
sign	签名（参考本页签名算法）	String	用于验证接受信息的正确性	ef6e3c5c6ff45018e8c82fd66fb056dc
sign_type	签名类型	String	默认为MD5	MD5
如何验证
请根据签名算法，验证自己生成的签名与参数中传入的签名是否一致，如果一致则说明是由官方向您发送的真实信息
注意事项
1.收到回调信息后请返回“success”，否则程序将判定您的回调地址未正确通知到。

2.同样的通知可能会多次发送给商户系统。商户系统必须能够正确处理重复的通知。

3.推荐的做法是，当收到通知进行处理时，首先检查对应业务数据的状态，判断该通知是否已经处理过，如果没有处理过再进行处理，如果处理过直接返回结果成功。在对业务数据进行状态检查和处理之前，要采用数据锁进行并发控制，以避免函数重入造成的数据混乱。

4.特别提醒：商户系统对于支付结果通知的内容一定要做签名验证,并校验返回的订单金额是否与商户侧的订单金额一致，防止数据泄漏导致出现“假通知”，造成资金损失。

5.对后台通知交互时，如果平台收到商户的应答不是纯字符串success或超过5秒后返回时，平台认为通知失败，平台会通过一定的策略（通知频率为0/15/15/30/180/1800/1800/1800/1800/3600，单位：秒）间接性重新发起通知，尽可能提高通知的成功率，但不保证通知最终能成功。

MD5签名算法
1、将发送或接收到的所有参数按照参数名ASCII码从小到大排序（a-z），sign、sign_type、和空值不参与签名！

2、将排序后的参数拼接成URL键值对的格式，例如 a=b&c=d&e=f，参数值不要进行url编码。

3、再将拼接好的字符串与商户密钥KEY进行MD5加密得出sign签名参数，sign = md5 ( a=b&c=d&e=f + KEY ) （注意：+ 为各语言的拼接符，不是字符！），md5结果为小写。

4、具体签名与发起支付的示例代码可下载SDK查看。