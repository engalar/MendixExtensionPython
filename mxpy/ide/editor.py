from mxpy import context

def open_by_id(unit_id):
    """
    通过 unit id 打开对应的编辑器
    
    Args:
        unit_id (str): Mendix 单元的唯一标识符
        
    Returns:
        bool: 打开是否成功
    """
    success, unit = context.currentApp.TryGetAbstractUnitById(unit_id, None)
    if success:
        # TryOpenEditor为内置函数
        return TryOpenEditor(unit)
    return False

TryOpenEditor = None