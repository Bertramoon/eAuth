# eAuth

基于RBAC的身份认证与访问控制系统【后端部分】—— 基于python3的flask框架(使用apiflask插件)

后端部分链接: [https://github.com/Bertramoon/eAuth-front](https://github.com/Bertramoon/eAuth-front )

## 基本项目结构

列举重要的文件并对有必要的部分加以说明

/EAUTH/EAUTH
|   constant.py
|   extensions.py
|   log_config.yaml
|   settings.py【存储系统的重要配置，部分配置从环境变量中读取】
|   __init__.py
|
+---auth【认证模块】
|   |   api.py【接口】
|   |   models.py【数据库模型定义】
|   |   schemas.py【输入输出模型定义】
|
+---base
|   |   schemas.py
|   |   validators.py
|   |   __init__.py
|
+---config【配置模块】
|   |   api.py
|   |   __init__.py
|   |
|   +---schemas
|   |   |   api.py
|   |   |   role.py
|   |   |   user.py
|   |   |   __init__.py
|
+---log
|   |   api.py
|   |   models.py
|   |   schemas.py
|   |   __init__.py
|
+---schedule
|   |   auth.py
|   |   __init__.py
|
+---templates
|   \---emails
|           register.html
|           register.txt
|           reset.html
|           reset.txt
|
+---utils
|   |   auth.py
|   |   decorator.py
|   |   email.py
|   |   message.py
|   |   model.py
|   |   tool.py
|   |   __init__.py


## 构建与初始化

### 安装依赖包

```shell
pip install -r requirements.txt
```

### 创建数据库和数据表

```shell
flask initdb --drop
```


## 设计与实现

### 功能设计

### 数据设计

### 质量设计

#### 性能

##### 缓存设计

核心鉴权接口使用内存缓存，其他地方不用缓存

#### 安全

##### 机密性

###### 用户管理

1、创建用户
- 用户名校验
- 口令生成
- 邮箱确认

2、密码管理
- 密码存储
- 密码修改
- 密码找回

3、登录登出
- 登录安全设计
- 会话安全设计

4、禁用用户
- 安全设计（令账号和会话失效）

###### 身份认证与访问控制
- 身份认证算法

##### 完整性

##### 不可抵赖性

###### 审计日志

eAuth的审计日志主要有操作日志和登录日志。

1、操作日志记录用户的操作（本系统主要是API配置、角色配置、为用户授权），包括：

- 操作人
- 客户端IP
- 操作资源对象id
- 操作类型（请求方法和接口名）
- 操作结果
- 响应码
- 请求内容
- 响应内容
- 操作时间

PS:

1)操作资源对象id有且仅有一个。一方面是基于设计，RESTFul风格是基于资源操作的，在本系统，每个接口仅操作某一类对象，同时，规定了只会有一个路径参数。另一方面，接口便于搜索查询

2)操作类型中记录的接口名称是按照flask中的格式的，例如`/api/config/role/<int:role_id>`

3)请求内容和响应内容参考接口AuditLogInterface，需要在schema中实现该接口

2、登录日志记录用户的登录登出等操作，包括：

- 操作人
- 客户端IP
- 操作（例如登录）
- 操作结果
- 操作时间


##### 可用性

- 接口限流
- 数据分页



