# Mendix 电商演示应用 - 设计文档

## 项目概述

**模块名称**: `ECommerceDemo`
**项目目标**: 演示 Mendix MCP 工具的各种功能，包括实体、属性、关联、枚举、常量、微流和页面。

## 领域模型设计

### 实体关系图

```
Customer (客户) ←→ Order (订单) ←→ OrderLine (订单明细) ←→ Product (产品) ←→ Category (类别)
    └────────────────────────────────────────────────────────────────────────┘
                                      多对多关系
```

### 1. Customer (客户实体)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| Name | String | - | 客户名称 |
| Email | String | - | 邮箱 |
| Phone | String | - | 电话 |
| Address | String | - | 地址 |
| IsActive | Boolean | true | 是否激活 |
| RegistrationDate | DateTime | [%CurrentDateTime%] | 注册日期 |

**关联**:
- `Customer_Order` → Order (ReferenceSet, Owner: Both) - 一对多

### 2. Product (产品实体)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| Name | String | - | 产品名称 |
| Description | String | - | 描述 |
| Price | Decimal | - | 价格 |
| Stock | Integer | 0 | 库存量 |
| SKU | String | - | 产品编码 |
| IsActive | Boolean | true | 是否上架 |
| CreatedDate | DateTime | [%CurrentDateTime%] | 创建时间 |

**关联**:
- `Product_Category` → Category (ReferenceSet, Owner: Both) - 多对多

### 3. Category (类别实体)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| Name | String | - | 类别名称 |
| Description | String | - | 描述 |
| Code | String | - | 类别代码 |

**关联**:
- `Category_Product` → Product (ReferenceSet, Owner: Both) - 多对多

### 4. Order (订单实体)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| OrderNumber | AutoNumber | - | 订单号 (自动编号) |
| OrderDate | DateTime | [%CurrentDateTime%] | 订单日期 |
| TotalAmount | Decimal | - | 总金额 |
| Status | Enumeration | - | 订单状态 (枚举) |
| PaymentMethod | Enumeration | - | 支付方式 (枚举) |
| Notes | String | - | 备注 |
| IsPaid | Boolean | false | 是否已付款 |
| ShippedDate | DateTime | - | 发货时间 |

**关联**:
- `Order_Customer` → Customer (Reference) - 多对一
- `Order_OrderLine` → OrderLine (ReferenceSet) - 一对多

### 5. OrderLine (订单明细实体)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| Quantity | Integer | - | 数量 |
| UnitPrice | Decimal | - | 单价 |
| Subtotal | Decimal | - | 小计 |
| Discount | Decimal | 0 | 折扣 |

**关联**:
- `OrderLine_Order` → Order (Reference) - 多对一
- `OrderLine_Product` → Product (Reference) - 多对一

## 枚举设计

### OrderStatus (订单状态)

| 值名称 | Caption | 说明 |
|--------|---------|------|
| Pending | 待处理 | 订单已创建，待处理 |
| Confirmed | 已确认 | 订单已确认 |
| Processing | 处理中 | 订单处理中 |
| Shipped | 已发货 | 订单已发货 |
| Delivered | 已送达 | 订单已送达 |
| Cancelled | 已取消 | 订单已取消 |
| Returned | 已退货 | 订单已退货 |

**完整路径**: `ECommerceDemo/OrderStatus`

### PaymentMethod (支付方式)

| 值名称 | Caption | 说明 |
|--------|---------|------|
| CreditCard | 信用卡 | 信用卡支付 |
| DebitCard | 借记卡 | 借记卡支付 |
| PayPal | PayPal | PayPal 支付 |
| WeChatPay | 微信支付 | 微信支付 |
| Alipay | 支付宝 | 支付宝支付 |
| CashOnDelivery | 货到付款 | 货到付款 |

**完整路径**: `ECommerceDemo/PaymentMethod`

## 常量设计

| 常量名 | 类型 | 默认值 | 暴露给客户端 | 说明 |
|--------|------|--------|--------------|------|
| TaxRate | Decimal | 0.10 | 是 | 税率 10% |
| CurrencySymbol | String | ¥ | 是 | 货币符号 |
| DefaultPageSize | Integer | 20 | 否 | 默认分页大小 |

**完整路径**:
- `ECommerceDemo/TaxRate`
- `ECommerceDemo/CurrencySymbol`
- `ECommerceDemo/DefaultPageSize`

## 微流设计

### 1. CalculateOrderTotal (计算订单总额)

**路径**: `ECommerceDemo/CalculateOrderTotal`
**返回类型**: `Decimal`
**参数**:
- `Order`: `ECommerceDemo.Order` - 订单对象

**功能**:
1. 通过关联 `Order_OrderLine` 获取订单的所有订单明细
2. 对所有明细的 `Subtotal` 属性求和
3. 返回总金额

**关键活动**:
- Retrieve (Association) - 获取订单明细列表
- AggregateList (Sum) - 汇总小计

---

### 2. CreateSimpleOrder (创建简单订单)

**路径**: `ECommerceDemo/CreateSimpleOrder`
**返回类型**: `ECommerceDemo.Order`
**参数**:
- `CustomerName`: `String` - 客户名称

**功能**:
1. 创建新的客户对象，设置名称
2. 创建新的订单对象
3. 建立订单与客户的关联
4. 提交到数据库

**关键活动**:
- CreateObject (Customer) - 创建客户
- CreateObject (Order) - 创建订单
- Set Association - 建立关联

---

### 3. GetActiveProducts (获取激活产品)

**路径**: `ECommerceDemo/GetActiveProducts`
**返回类型**: `List(ECommerceDemo.Product)`
**参数**: 无

**功能**:
1. 从数据库检索所有 `IsActive = true` 的产品
2. 返回产品列表

**关键活动**:
- Retrieve (Database) - XPath 约束查询

---

### 4. AddProductToOrder (添加产品到订单)

**路径**: `ECommerceDemo/AddProductToOrder`
**返回类型**: `ECommerceDemo.OrderLine`
**参数**:
- `Order`: `ECommerceDemo.Order`
- `Product`: `ECommerceDemo.Product`
- `Quantity`: `Integer`

**功能**:
1. 创建新的订单明细
2. 设置关联到订单和产品
3. 从产品复制价格到单价
4. 设置数量

**关键活动**:
- CreateObject - 创建订单明细
- Set Association - 设置双向关联
- Set Attribute - 从关联对象获取值 (`$Product/Price`)

---

### 5. GetProductsByCategory (按类别获取产品)

**路径**: `ECommerceDemo/GetProductsByCategory`
**返回类型**: `List(ECommerceDemo.Product)`
**参数**:
- `Category`: `ECommerceDemo.Category`

**功能**:
1. 通过关联获取类别下的所有产品
2. 返回产品列表

**关键活动**:
- Retrieve (Association) - 通过关联检索

---

### 6. FindCustomerByEmail (按邮箱查找客户)

**路径**: `ECommerceDemo/FindCustomerByEmail`
**返回类型**: `ECommerceDemo.Customer`
**参数**:
- `Email`: `String`

**功能**:
1. 使用 XPath 从数据库查询客户
2. 返回第一个匹配的客户

**关键活动**:
- Retrieve (Database) - XPath 查询 `[Email = $Email]`
- RetrieveJustFirstItem = true

## 页面设计

### 1. ProductOverview (产品列表页)

**路径**: `ECommerceDemo/Pages/ProductCatalog/ProductOverview.page`
**说明**: 展示所有产品的列表视图

### 2. OrderOverview (订单列表页)

**路径**: `ECommerceDemo/Pages/Orders/OrderOverview.page`
**说明**: 展示所有订单的列表视图

### 3. OrderDetail (订单详情页)

**路径**: `ECommerceDemo/Pages/Orders/OrderDetail.page`
**说明**: 显示单个订单的详细信息，包括订单明细

### 4. CustomerOverview (客户列表页)

**路径**: `ECommerceDemo/Pages/Customers/CustomerOverview.page`
**说明**: 展示所有客户的列表视图

### 5. CustomerDetail (客户详情页)

**路径**: `ECommerceDemo/Pages/Customers/CustomerDetail.page`
**说明**: 显示单个客户的详细信息

## 文件夹结构

```
ECommerceDemo/
├── Pages/
│   ├── ProductCatalog/
│   │   └── ProductOverview.page
│   ├── Orders/
│   │   ├── OrderOverview.page
│   │   └── OrderDetail.page
│   └── Customers/
│       ├── CustomerOverview.page
│       └── CustomerDetail.page
├── Flows/
│   ├── CalculateOrderTotal.mf
│   ├── CreateSimpleOrder.mf
│   ├── GetActiveProducts.mf
│   ├── AddProductToOrder.mf
│   ├── GetProductsByCategory.mf
│   └── FindCustomerByEmail.mf
└── System/
    ├── OrderStatus.enumeration
    └── PaymentMethod.enumeration
```

## 工具使用映射

| Mendix MCP 工具 | 使用场景 | 演示内容 |
|----------------|----------|----------|
| `ensure_modules` | 步骤 1 | 创建 ECommerceDemo 模块 |
| `create_enumerations` | 步骤 2 | 创建订单状态、支付方式枚举 |
| `create_entities` | 步骤 3 | 创建 5 个实体、属性和关联 |
| `create_constants` | 步骤 4 | 创建税率、货币符号等常量 |
| `ensure_microflows` | 步骤 5 | 创建 6 个业务逻辑微流 |
| `ensure_pages` | 步骤 6 | 创建 5 个页面 |
| `create_folders` | 步骤 7 | 组织文件夹结构 |
| `open_document` | 验证 | 打开并验证创建的文档 |

## 数据类型演示总结

### 属性类型
- ✅ **String**: 名称、地址、邮箱
- ✅ **Integer**: 数量、库存
- ✅ **Decimal**: 价格、金额
- ✅ **Boolean**: 是否激活、是否付款
- ✅ **DateTime**: 日期时间字段
- ✅ **AutoNumber**: 订单号
- ✅ **Enumeration**: 订单状态、支付方式

### 关联类型
- ✅ **Reference** (多对一): Order → Customer
- ✅ **ReferenceSet** (一对多): Customer → Order
- ✅ **ReferenceSet** (多对多): Product ↔ Category

### 微流活动类型
- ✅ **Retrieve** (Association/Database)
- ✅ **CreateObject**
- ✅ **Change**
- ✅ **Commit**
- ✅ **AggregateList** (Sum)
- ✅ **XPath 约束查询**

## 创建验证

所有组件已通过以下方式验证：
1. 创建命令返回成功
2. 使用 `open_document` 打开并验证关键文档：
   - ✅ `ECommerceDemo.CalculateOrderTotal` - 微流成功打开
   - ✅ `ECommerceDemo.ProductOverview` - 页面成功打开
   - ✅ `ECommerceDemo.OrderStatus` - 枚举找到

## 项目信息

- **当前项目**: AggDemo
- **创建时间**: 2026-01-12
- **模块状态**: ✅ 所有组件创建成功
