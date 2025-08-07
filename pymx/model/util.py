class TransactionManager:
    """with TransactionManager(current_app, f"your transaction name"):"""

    def __init__(self, app, transaction_name):
        self.app = app
        self.name = transaction_name
        self.transaction = None

    def __enter__(self):
        self.transaction = self.app.StartTransaction(self.name)
        return self.transaction

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.transaction.Commit()
        else:
            self.transaction.Rollback()
        self.transaction.Dispose()
        return False  # 允许异常继续传播


def callAsType(model, obj, type, methodName, params=None):
    """
    获取对象方法并调用
    参数：
    model: 模型对象
    obj: 对象
    type: 对象类型
    methodName: 方法名
    params: 方法参数
    """
    helpObj = model.Create[type]()
    mi = helpObj.GetType().GetMethod(methodName)
    return mi.Invoke(obj, params)

# cast property


def property_cast(model,obj, type, propertyName):
    helpObj = model.Create[type]()
    property = helpObj.GetType().GetProperty(propertyName)
    return (property != None, property.GetValue(obj) if property else None)
