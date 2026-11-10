"""
邮件发送工具（找回密码验证码等）
未配置 SMTP 时进入开发模式：不真正发信，由接口返回验证码便于本地调试。
"""
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from config import Config


def is_mail_configured():
    return bool(Config.MAIL_HOST and Config.MAIL_USER and Config.MAIL_PASSWORD)


def send_email(to_addr, subject, body):
    """
    发送纯文本邮件。
    :return: (ok: bool, message: str)
    """
    if not is_mail_configured():
        return False, '未配置邮件服务（开发模式）'

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(Config.MAIL_FROM or Config.MAIL_USER)
    msg['To'] = Header(to_addr)
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        if Config.MAIL_USE_SSL:
            server = smtplib.SMTP_SSL(Config.MAIL_HOST, Config.MAIL_PORT, timeout=20)
        else:
            server = smtplib.SMTP(Config.MAIL_HOST, Config.MAIL_PORT, timeout=20)
            if Config.MAIL_USE_TLS:
                server.starttls()
        server.login(Config.MAIL_USER, Config.MAIL_PASSWORD)
        server.sendmail(Config.MAIL_USER, [to_addr], msg.as_string())
        server.quit()
        return True, '邮件已发送'
    except Exception as exc:
        return False, f'邮件发送失败: {exc}'


def build_reset_code_mail(code, expire_minutes=10):
    subject = '【心屿】找回密码验证码'
    body = (
        f'您好，\n\n'
        f'您正在找回心屿平台账号密码，验证码为：{code}\n'
        f'有效期 {expire_minutes} 分钟，请勿泄露给他人。\n'
        f'如非本人操作，请忽略本邮件。\n\n'
        f'— 心屿校园心理健康服务平台'
    )
    return subject, body
