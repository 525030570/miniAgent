import os
import json
import pymysql
from dotenv import load_dotenv




def sql_inter(sql_query, g='globals()'):
    """
    用于执行一段SQL代码，并最终获取SQL代码执行结果，\
    核心功能是将输入的SQL代码传输至MySQL环境中进行运行，\
    并最终返回SQL代码运行结果。需要注意的是，本函数是借助pymysql来连接MySQL数据库。
    :param sql_query: 字符串形式的SQL查询语句，用于执行对MySQL中telco_db数据库中各张表进行查询，并获得各表中的各类相关信息
    :param g: g，字符串形式变量，表示环境变量，无需设置，保持默认参数即可
    :return：sql_query在MySQL中的运行结果。
    """
    print("正在调用sql_inter工具运行SQL代码...")
    load_dotenv(override=True)
    host = os.getenv('HOST')
    user = os.getenv('USER')
    mysql_pw = os.getenv('MYSQL_PW')
    db = os.getenv('DB_NAME')
    port = os.getenv('PORT')
    
    connection = pymysql.connect(
        host = host,  
        user = user, 
        passwd = "19920229",  
        db = db,
        port = int(port),
        charset='utf8',
    )
    
    try:
        with connection.cursor() as cursor:
            sql = sql_query
            cursor.execute(sql)
            results = cursor.fetchall()
            print("SQL代码已顺利运行，正在整理答案...")

    finally:
        connection.close()

    return json.dumps(results)


sql_inter_args = '{"sql_query": "SHOW TABLES;"}'

sql_inter_tool = {
    "type": "function",
    "function": {
        "name": "sql_inter",
        "description": (
            "当用户需要进行数据库查询工作时，请调用该函数。"
            "该函数用于在指定MySQL服务器上运行一段SQL代码，完成数据查询相关工作，"
            "并且当前函数是使用pymsql连接MySQL数据库。"
            "本函数只负责运行SQL代码并进行数据查询，若要进行数据提取，则使用另一个extract_data函数。"
            "同时需要注意，编写外部函数的参数消息时，必须是满足json格式的字符串，例如以下形式字符串就是合规字符串："
            f"{sql_inter_args}"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The SQL query to execute in MySQL database."
                },
                "g": {
                    "type": "string",
                    "description": "Global environment variables, default to globals().",
                    "default": "globals()"
                }
            },
            "required": ["sql_query"]
        }
    }
}