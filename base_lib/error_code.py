# coding: utf-8
# ::::::::::::::::::
# 错误信息及code列表

ERROR_CODE = {

    # 第三方或者其他服务错误
    "DBERR"               : "2000",
    "THIRDERR"            : "2001",
    "DATAERR"             : "2003",
    "IOERR"               : "2004",
    "REDISERR"            : "2005",
    "SERVERERR"           : "2006",

    # 返回内容错误
    "NODATA"              : "2300",
    "DATAEXIST"           : "2301",
    "CONTENTERR"          : "2302",
    "NOT_FOUND"           : "404",

    # 未知错误
    "UNKOWNERR"           : "2400",

    # 参数错误
    "PARAMERR"            : "2401",

    # User 相关
    "SESSIONERR"          : "2100",
    "USERERR"             : "2102",
    "ROLEERR"             : "2103",
    "PWDERR"              : "2104",
    "BALANCEERR"          : "2110", 

    # 验证失败
    "VERIFYERR"           : "2105",

}


ERROR_MSG = { 
    # 第三方或者其他服务错误
    "DBERR"               : "数据库查询错误",
    "THIRDERR"            : "第三方系统错误",
    "DATAERR"             : "数据错误",
    "IOERR"               : "文件读写错误",
    "REDISERR"            : "REDIS错误",
    "SERVERERR"           : "内部错误",

    # 返回内容错误
    "NODATA"              : "无数据",
    "DATAEXIST"           : "数据已存在",
    "CONTENTERR"          : "内容错误",
    "NOT_FOUND"           : "未知请求",

    # 未知错误
    "UNKOWNERR"           : "未知错误",

    # 参数错误
    "PARAMERR"            : "参数错误",

    # User 相关
    "SESSIONERR"          : "未登录",
    "USERERR"             : "用户不存在",
    "ROLEERR"             : "用户身份错误",
    "PWDERR"              : "密码错误",
    "BALANCEERR"          : "钱包账号余额不足", 

    # 验证失败
    "VERIFYERR"           : "验证码错误",
}


ERROR_MSG_CODE = {

    # 第三方或者其他服务错误
    "数据库查询错误"      : "2000",
    "第三方系统错误"      : "2001",
    "数据错误"            : "2003",
    "文件读写错误"        : "2004",
    "REDIS错误"           : "2005",
    "内部错误"            : "2006",

    # 返回内容错误
    "无数据"              : "2300",
    "数据已存在"          : "2301",
    "内容错误"            : "2302",
    "未知请求"            : "404",

    # 未知错误
    "未知错误"            : "2400",

    # 参数错误
    "参数错误"            : "2401",

    # User 相关
    "未登录"              : "2100",
    "用户不存在"          : "2102",
    "用户身份错误"        : "2103",
    "密码错误"            : "2104",
    "钱包账号余额不足"    : "2110",

    # 验证失败
    "验证码错误"          : "2105",

}

