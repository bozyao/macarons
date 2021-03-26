# coding: utf-8


class GeneralError(Exception):

    def __init__(self, error_msg):
        super(GeneralError, self).__init__()
        self.error_msg = error_msg

    def __str__(self):
        return self.error_msg


if __name__ == "__main__":
    try:
        raise GeneralError('客户异常')
    except Exception as e:
        print(e)
