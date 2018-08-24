import os  # 导入系统模块
import socket  # 导入 socket包
from multiprocessing import Process  # 导入多进程模块


def set_status(fun):
    """
    返回值的装饰器, 增加User-Agent判断代理是否异常， 返回403
    :param fun:
    :return:
    """

    def change(self, *args, **kwargs):
        if len(self.request_dict['User-Agent']) < 60:
            return 403
        else:
            return fun(self, *args, **kwargs)

    return change


class WebServer(object):
    BASE_DIR = os.path.join(os.getcwd(), 'static')  # 查询文件夹， 用来查找访问的文件
    RESPONSE_STATUS = {200: 'OK', 404: 'Not Found', 403: 'Forbid'}  # 设置响应行可选返回状态码， 只选择了部分做演示

    def __init__(self, port=8080):
        """
        初始化参数
        :param port:
        """
        self.soc = self.create_server(port)  # 初始化socket对象
        self.new_fd: socket.socket = ...  # 方便pycharm提示,防止pycharm报波浪线
        self.request_dict = {}  # 设置空字典， 用于存储处理过后的请求头
        # 设置响应头，因为可能有多个Set-Cookie， 所以用列表中的元组存储
        self.response_dict = [('Server', 'my_server'), ('Content-Type', 'text/html; charset=utf-8')]
        os.chdir(self.BASE_DIR)  # 改变查找文件路径

    # 创建socket对象
    def create_server(self, port):
        """
        用来初始化server对象
        :return:
        """
        self.soc = socket.socket()  # 创建socket对象
        self.soc.bind(('', port))  # 绑定套接字到address， 一般为 ip+port， 并且host一般是127.0.0.1或者不填(等内核分配)，一般无权绑定非本机ip
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 接续服务器突然宕掉时，端口暂时不能使用的问题
        self.soc.listen(5)  # 转为监听状态 服务器必须
        return self.soc

    # 开启多进程
    def runserver(self):
        """
        多进程处理请求
        :return:
        """
        while True:
            self.new_fd, _ = self.soc.accept()  # 从缓存中读取新的请求
            fd = Process(target=self.handler)  # 转到子进程中执行
            fd.start()  # 开启进程
            self.new_fd.close()  # 去掉主进程引用

    # 接收请求头
    def handler(self):
        """
        处理发送过来的信息
        :return:
        """
        print('新的链接到来，', self.new_fd)
        buf: bytes = self.new_fd.recv(1024)  # 读取部分数据，主要用来处理请求行和请求头
        if buf:
            new_buf = buf.decode('utf8')  # 将二进制数据转成str
            # 解析字符串
            self._request_handler(new_buf)

    # 解析请求头
    def _request_handler(self, data: str):
        """
        浏览器请求 格式固定
        请求行: GET / HTTP/1.1\r\n
        请求头: Host: 127.0.0.1\r\n
               User-Agent: Mozilla5.0...\r\n
        请求体: 基本为固定为POST 的内容， 此处不演示
        :param data:
        :return:
        """
        data = data.splitlines()  # 进行行分割
        request_head = data.pop(0).strip()  # 接受请求行
        self.request_dict['Method'], self.request_dict['Path'], _ = request_head.split(' ')  # 生成请求行字典
        # 遍历data部分,得到请求头信息 Host: 127.0.0.1 列表中的格式
        new_data = {x[0]: x[1] for x in [i.split(':') for i in data if ': ' in i]}
        # 更新字典
        self.request_dict.update(new_data)
        # 获取请求路径
        self.filename = self.request_dict['Path'][1:]  # 获取请求的url
        self._response_handler()

    # 发送响应头
    def _response_handler(self):

        """
        响应体的格式
        响应行: HTTP/1.1 200 OK\r\n
        响应头: Content-Type:text/html; charset=utf-8\r\n
               Server: My_server\r\n
        响应体: HTML/JSON/JPG/PNG/MP3.....
        """
        self.status = self._check_request()
        response_head = f"HTTP/1.1 {self.status} {self.RESPONSE_STATUS[self.status]}\r\n"  # 组成请求行
        response_content = ''.join([i[0] + ': ' + i[1] + '\r\n' for i in self.response_dict])  # 组成请求头
        response_end = '\r\n'  # 换行  头部结束
        self.response = response_head + response_content + response_end
        # 发送请求头信息
        self.new_fd.send(self.response.encode('utf8'))
        self.send_response()

    # 发送响应体内容
    def send_response(self):
        if self.status == 200:
            # 正常访问页面
            with open(self.filename, 'rb') as f:
                self.new_fd.send(f.read())
        elif self.status == 404:
            # 打开404页面
            with open('404.html', 'rb') as f:
                self.new_fd.send(f.read())
        elif self.status == 403:
            self.new_fd.send('ForForForbid'.encode('utf8'))

    @set_status
    def _check_request(self):
        """
        给出返回值， 403用装饰器装饰
        :return:
        """
        if os.path.isfile(self.filename):
            return 200
        else:
            return 404


if __name__ == '__main__':
    test = WebServer()
    test.runserver()
