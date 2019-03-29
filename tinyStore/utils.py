# coding=utf-8
def get_no_empty_dict(dic):
    """
    筛选出字典中值不为None的项，如果键对应的是字典，就递归筛选
    :param dic:
    :return:
    """
    d = dic.copy()
    for key, value in dic.iteritems():
        if value is None:
            d.__delitem__(key)
        elif isinstance(value, dict):
            d[key] = get_no_empty_dict(value)
    return d