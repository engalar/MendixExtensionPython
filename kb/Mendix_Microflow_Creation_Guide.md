# Mendix 微流创建工具使用指南

> 基于 `mcp__remote_studiopro__ensure_microflows` 工具的实践经验总结

## 🔧 核心格式规范

### 1. FullPath 格式
```json
"FullPath": "ModuleName/MicroflowName"  // ✅ 正确：使用 / 分隔
"FullPath": "ModuleName/SubFolder1/SubFolder2/MyMicroflow"  // ✅ 正确：深文件夹
"FullPath": "ModuleName.MicroflowName"  // ❌ 错误：不要用 .
```

**错误示例**:
```
Value error, FullPath 必须至少包含 'ModuleName/MicroflowName'
```

### 2. ReturnType 格式
```json
// 基础类型
"ReturnType": "String"
"ReturnType": "Integer"
"ReturnType": "Boolean"
"ReturnType": "Void"

// 实体类型
"ReturnType": "DemoModule.Customer"

// 列表类型（仅限实体）
"ReturnType": "List(DemoModule.Customer)"
```

### 3. Parameters 类型定义
```json
// 基础类型
{"Name": "myString", "Type": "String"}
{"Name": "myInt", "Type": "Integer"}
{"Name": "myBool", "Type": "Boolean"}

// 实体类型
{"Name": "customer", "Type": "DemoModule.Customer"}

// ❌ 避免：List(String) 这类基础类型的列表可能有问题
```

## 📋 Activities 必填字段速查表

| ActivityType | 必填字段 | 可选字段 | 说明 |
|---|---|---|---|
| **CreateObject** | `EntityName`, `OutputVariable`, `InitialValues` | `Commit`, `RefreshClient` | 创建新对象 |
| **Retrieve** | `EntityName`, `OutputVariable`, `SourceType` | `XPathConstraint`, `RetrieveJustFirstItem`, `Sorting` | 从数据库或关联获取 |
| **Change** | `VariableName`, `Changes` | `Commit`, `RefreshClient`, `EntityName` | 修改对象属性/关联 |
| **Commit** | `VariableName` | - | 提交到数据库 |
| **Delete** | `VariableName` | - | 删除对象 |
| **Rollback** | `VariableName` | - | 回滚未提交的更改 |
| **CreateList** | `EntityName`, `OutputVariable` | - | 创建空列表 |
| **AggregateList** | `Function`, `ListVariable`, `OutputVariable` | `Attribute` | 聚合操作 |
| **ListOperation** | `OperationType`, `ListVariable` | `BinaryOperationListVariable` | 列表操作 |
| **FilterList** | `ListVariable`, `FilterBy`, `MemberName`, `Expression` | `OutputVariable` | 过滤列表 |
| **SortList** | `ListVariable`, `Sorting` | `OutputVariable` | 排序列表 |
| **FindList** | `ListVariable`, `FindBy`, `MemberName` | `Expression`, `OutputVariable` | 查找元素 |

## ⚠️ 常见错误及解决方案

### 错误 1: FullPath 格式错误
```
Value error, FullPath 必须至少包含 'ModuleName/MicroflowName'
```
**原因**: 使用了 `.` 而非 `/` 分隔模块和微流名
**解决方案**:
```json
"FullPath": "DemoModule/Greeting"  // ✅ 正确
"FullPath": "DemoModule.Greeting"  // ❌ 错误
```

### 错误 2: 缺少必需的 EntityName
```
EntityName is required for CreateList
```
**原因**: CreateList 和 CreateObject 必须指定 `EntityName`
**解决方案**:
```json
{
  "ActivityType": "CreateObject",
  "EntityName": "DemoModule.Customer",  // ✅ 必须指定
  "OutputVariable": "Customer"
}
```

### 错误 3: List(String) 类型识别失败
```
The text 'String' is not a valid EntityIdentifier
```
**原因**: 系统期望列表类型使用实体（且在模型中存在）而非基础类型
**解决方案**:
- 使用实体类型的列表: `List(DemoModule.Customer)`
- 或使用聚合函数处理基础类型列表

### 错误 4: 字符串值未加引号
**原因**: 在 `ValueExpression` 中，字符串必须用单引号包裹
**解决方案**:
```json
"ValueExpression": "'Hello World'"  // ✅ 正确
"ValueExpression": "Hello World"    // ❌ 错误
"ValueExpression": "$Name"          // ✅ 变量不需要引号
```

### 错误 5: 变量引用未使用 $ 前缀
**原因**: 引用参数或变量时必须加 `$` 前缀
**解决方案**:
```json
"ValueExpression": "$customerName"  // ✅ 正确
"ValueExpression": "customerName"   // ❌ 错误
```

### 错误 6: ReturnExp 类型不匹配
**原因**: 返回表达式的类型与声明的 ReturnType 不一致
**解决方案**:
```json
{
  "ReturnType": "Integer",
  "ReturnExp": "$Count"  // ✅ 确保类型匹配
}
```

### 错误 7: 变量属性导航语法错误
**原因**: 访问对象属性时使用了错误的属性名格式
**解决方案**:
```json
// ✅ 推荐：使用简短属性名（不含模块前缀）
"ReturnExp": "'User ID: ' + toString($User/User_ID)"

// 如果是关联属性，则需要完整限定名
"ReturnExp": "'User ID: ' + toString($User/MyModule.User_ID)"
```

**注意**: 属性访问格式为 `$VariableName/AttributeName`，通常不需要模块前缀。如果遇到问题，可尝试使用完整限定名格式。

## ✅ 完整示例模板

### 示例 1: 创建简单对象
```json
{
  "FullPath": "MyModule/CreateUser",
  "ReturnType": "String",
  "ReturnExp": "'User ID: ' + toString($User/User_ID)",
  "Parameters": [
    {"Name": "name", "Type": "String"},
    {"Name": "age", "Type": "Integer"}
  ],
  "Activities": [
    {
      "ActivityType": "CreateObject",
      "EntityName": "MyModule.User",
      "OutputVariable": "User",
      "InitialValues": [
        {"AttributeName": "Name", "ValueExpression": "$name"},
        {"AttributeName": "Age", "ValueExpression": "$age"}
      ],
      "Commit": "Yes",
      "RefreshClient": false
    }
  ]
}
```

### 示例 2: 数据库查询
```json
{
  "FullPath": "MyModule/GetUserByName",
  "ReturnType": "MyModule.User",
  "ReturnExp": "$User",
  "Parameters": [
    {"Name": "name", "Type": "String"}
  ],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "User",
      "XPathConstraint": "[Name = $name]",
      "RetrieveJustFirstItem": true
    }
  ]
}
```

### 示例 3: 获取所有记录
```json
{
  "FullPath": "MyModule/GetAllUsers",
  "ReturnType": "List(MyModule.User)",
  "ReturnExp": "$UserList",
  "Parameters": [],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "UserList",
      "RetrieveJustFirstItem": false
    }
  ]
}
```

### 示例 4: 聚合统计
```json
{
  "FullPath": "MyModule/CountUsers",
  "ReturnType": "Integer",
  "ReturnExp": "$Count",
  "Parameters": [],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "UserList"
    },
    {
      "ActivityType": "AggregateList",
      "Function": "Count",
      "ListVariable": "UserList",
      "OutputVariable": "Count"
    }
  ]
}
```

### 示例 5: 修改对象
```json
{
  "FullPath": "MyModule/UpdateUserEmail",
  "ReturnType": "Void",
  "ReturnExp": "",
  "Parameters": [
    {"Name": "userId", "Type": "Integer"},
    {"Name": "newEmail", "Type": "String"}
  ],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "User",
      "XPathConstraint": "[ID = $userId]",
      "RetrieveJustFirstItem": true
    },
    {
      "ActivityType": "Change",
      "VariableName": "User",
      "Changes": [
        {"AttributeName": "Email", "ValueExpression": "$newEmail"}
      ],
      "Commit": "Yes",
      "RefreshClient": false
    }
  ]
}
```

### 示例 6: 删除对象
```json
{
  "FullPath": "MyModule/DeleteUser",
  "ReturnType": "Boolean",
  "ReturnExp": "$isDeleted",
  "Parameters": [
    {"Name": "userId", "Type": "Integer"}
  ],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "User",
      "XPathConstraint": "[ID = $userId]",
      "RetrieveJustFirstItem": true
    },
    {
      "ActivityType": "Delete",
      "VariableName": "User"
    }
  ]
}
```

### 示例 7: 带排序的查询
```json
{
  "FullPath": "MyModule/GetUsersSortedByAge",
  "ReturnType": "List(MyModule.User)",
  "ReturnExp": "$UserList",
  "Parameters": [],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "UserList",
      "Sorting": [
        {"AttributeName": "Age", "Ascending": true}
      ]
    }
  ]
}
```

### 示例 8: 条件过滤
```json
{
  "FullPath": "MyModule/GetAdultUsers",
  "ReturnType": "List(MyModule.User)",
  "ReturnExp": "$AdultList",
  "Parameters": [],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "MyModule.User",
      "SourceType": "Database",
      "OutputVariable": "AllUsers"
    },
    {
      "ActivityType": "FilterList",
      "ListVariable": "AllUsers",
      "FilterBy": "Attribute",
      "MemberName": "Age",
      "Expression": ">= 18",
      "OutputVariable": "AdultList"
    }
  ]
}
```

### 示例 9: 综合订单处理（完整流程）
本示例综合展示了枚举赋值、关联设置、关联查询、聚合统计等操作。

```json
{
  "FullPath": "DemoModule/SubFolder1/SubFolder2/ProcessOrderWithValidation",
  "ReturnType": "String",
  "ReturnExp": "'Order created for ' + $customerName + '. Total: ' + toString($NewOrder/TotalAmount) + '. This is order #' + toString($Customer/TotalOrders)",
  "Parameters": [
    {"Name": "customerName", "Type": "String"},
    {"Name": "productName", "Type": "String"},
    {"Name": "quantity", "Type": "Integer"}
  ],
  "Activities": [
    {
      "ActivityType": "Retrieve",
      "EntityName": "DemoModule.Customer",
      "OutputVariable": "Customer",
      "SourceType": "Database",
      "XPathConstraint": "[Name = $customerName]",
      "RetrieveJustFirstItem": true
    },
    {
      "ActivityType": "CreateObject",
      "EntityName": "DemoModule.Order",
      "OutputVariable": "NewOrder",
      "InitialValues": [
        {
          "AttributeName": "Status",
          "ValueExpression": "DemoModule.OrderStatus.Pending"
        }
      ],
      "Commit": "No"
    },
    {
      "ActivityType": "Retrieve",
      "EntityName": "DemoModule.Product",
      "OutputVariable": "Product",
      "SourceType": "Database",
      "XPathConstraint": "[Name = $productName]",
      "RetrieveJustFirstItem": true
    },
    {
      "ActivityType": "Change",
      "VariableName": "NewOrder",
      "EntityName": "DemoModule.Order",
      "Changes": [
        {
          "AssociationName": "DemoModule.Order_Product",
          "Action": "Set",
          "ValueExpression": "$Product"
        }
      ],
      "Commit": "No"
    },
    {
      "ActivityType": "Retrieve",
      "EntityName": "DemoModule.Order",
      "OutputVariable": "CustomerOrders",
      "SourceType": "Association",
      "SourceVariable": "Customer",
      "AssociationName": "DemoModule.Order_Customer"
    },
    {
      "ActivityType": "AggregateList",
      "Function": "Count",
      "ListVariable": "CustomerOrders",
      "OutputVariable": "OrderCount"
    },
    {
      "ActivityType": "Change",
      "VariableName": "Customer",
      "EntityName": "DemoModule.Customer",
      "Changes": [
        {
          "AttributeName": "TotalOrders",
          "ValueExpression": "$OrderCount + 1"
        }
      ],
      "Commit": "Yes"
    }
  ]
}
```

**本示例要点说明：**
- **枚举赋值**：`Status` 字段赋值为 `DemoModule.OrderStatus.Pending`
- **关联设置**：通过 `AssociationName` + `Action: "Set"` 将订单与产品关联
- **关联查询**：使用 `SourceType: "Association"` 查询客户的所有订单
- **聚合统计**：统计客户订单数量并更新客户的 `TotalOrders` 字段

## 🎯 一次成功的关键检查点

创建微流前，按此清单检查：

### 结构检查
- [ ] FullPath 使用 `/` 分隔模块和微流名
- [ ] ReturnType 类型正确（String/Integer/Boolean/Void/Entity/List(Entity)）
- [ ] ReturnExp 与 ReturnType 类型匹配
- [ ] Void 类型的 ReturnExp 应为空字符串 `""`

### 参数检查
- [ ] Parameters 中每个参数都有 Name 和 Type
- [ ] Type 使用正确的基础类型或实体类型

### 表达式检查
- [ ] 字符串值用单引号包裹: `'Hello'`
- [ ] 变量引用使用 `$` 前缀: `$myVar`
- [ ] 属性访问使用 `/`: `$Object/Module_Entity_Attribute`
- [ ] 类型转换函数: `toString()`, `parseInt()`, etc.

### Activity 检查
- [ ] CreateObject/Retrieve 指定了 EntityName
- [ ] 每个 Activity 的 OutputVariable 唯一
- [ ] Activities 按依赖顺序排列（先定义变量再使用）
- [ ] InitialValues 和 Changes 中的 ValueExpression 正确

### 关联检查
- [ ] AssociationName 使用完整限定名: `Module.AssociationName`
- [ ] SourceVariable 在 Retrieve-Association 中已定义

## 📝 常用 XPath 约束示例

```javascript
// 等于
"[Name = $name]"

// 不等于
"[Age != $age]"

// 大于小于
"[Age >= 18]"
"[Score > 60]"

// 逻辑与
"[Age >= 18 AND IsActive = true()]"

// 逻辑或
"[City = 'Beijing' OR City = 'Shanghai']"

// 包含
"[Namecontains($keyword)]"

// 开始于
"[Namestarts($prefix)]"
```

## 🔍 常用函数

```javascript
// 类型转换
toString($value)
parseInt($string)
parseFloat($string)

// 字符串操作
substring($string, $start, $length)
length($string)
toLowerCase($string)
toUpperCase($string)

// 日期时间
dateTime() currentDate() currentTime()

// 数学运算
round($number)
floor($number)
ceiling($number)
abs($number)
```

## 🔢 枚举值赋值

在 `CreateObject` 的 `InitialValues` 或 `Change` 的 `Changes` 中赋值枚举类型时，使用完整限定名格式。

### 格式
```json
{
  "AttributeName": "Status",
  "ValueExpression": "Module.EnumName.EnumValue"
}
```

### 示例
```json
{
  "ActivityType": "CreateObject",
  "EntityName": "DemoModule.Order",
  "OutputVariable": "Order",
  "InitialValues": [
    {
      "AttributeName": "Status",
      "ValueExpression": "DemoModule.OrderStatus.Pending"
    }
  ]
}
```

### 常见错误
```json
// ❌ 错误：未使用完整限定名
"ValueExpression": "Pending"

// ❌ 错误：使用字符串引号
"ValueExpression": "'DemoModule.OrderStatus.Pending'"

// ✅ 正确：完整限定名，无引号
"ValueExpression": "DemoModule.OrderStatus.Pending"
```

## 🔗 关联操作 (Association Operations)

在 `Change` 活动中设置对象关联时，需要使用 `AssociationName`、`Action` 和 `ValueExpression` 字段。

### 关联操作的 ChangeItem 格式

```json
{
  "AssociationName": "Module.AssociationName",
  "Action": "Set | Add | Remove",
  "ValueExpression": "$ObjectVariable"
}
```

### Action 类型说明

| Action | 说明 | 适用关联类型 |
|---|---|---|
| **Set** | 设置关联对象（覆盖） | Reference (一对一/多对一) |
| **Add** | 添加到关联集合 | ReferenceSet (一对多/多对多) |
| **Remove** | 从关联集合中移除 | ReferenceSet (一对多/多对多) |

### 示例 1: 设置单值关联 (Reference)
```json
{
  "ActivityType": "Change",
  "VariableName": "Order",
  "EntityName": "DemoModule.Order",
  "Changes": [
    {
      "AssociationName": "DemoModule.Order_Product",
      "Action": "Set",
      "ValueExpression": "$Product"
    }
  ],
  "Commit": "No"
}
```

### 示例 2: 添加到集合关联 (ReferenceSet)
```json
{
  "ActivityType": "Change",
  "VariableName": "Customer",
  "EntityName": "DemoModule.Customer",
  "Changes": [
    {
      "AssociationName": "DemoModule.Customer_Orders",
      "Action": "Add",
      "ValueExpression": "$NewOrder"
    }
  ],
  "Commit": "No"
}
```

### 示例 3: 从集合中移除
```json
{
  "ActivityType": "Change",
  "VariableName": "Customer",
  "EntityName": "DemoModule.Customer",
  "Changes": [
    {
      "AssociationName": "DemoModule.Customer_Orders",
      "Action": "Remove",
      "ValueExpression": "$OldOrder"
    }
  ],
  "Commit": "Yes"
}
```

### 重要说明

1. **关联名格式**：必须使用完整限定名 `Module.AssociationName`
2. **ValueExpression**：值为对象变量（如 `$Product`），不是 ID 或其他值
3. **Action 选择**：
   - `Reference` 类型关联只能使用 `Set`
   - `ReferenceSet` 类型关联使用 `Add` 或 `Remove`