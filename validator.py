import re
import dns.resolver
import smtplib
import socket

SENDER_EMAIL_DOMAIN = "gmail.com"
TIMEOUT = 5

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.org",
}

def is_valid_syntax(email):
    email_regex = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    return bool(email_regex.match(email))

def get_mx_servers(domain):
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return sorted([str(rdata.exchange) for rdata in mx_records],
                      key=lambda x: [r.preference for r in mx_records if str(r.exchange) == x][0])
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.Timeout, dns.resolver.NoNameservers):
        return []

def verify_email_via_smtp(email_address, mx_servers):
    if not mx_servers:
        return False, "NO_MX_RECORDS"

    for mx_server in mx_servers:
        try:
            with smtplib.SMTP(mx_server, 25, timeout=TIMEOUT) as server:
                server.set_debuglevel(0)
                server.ehlo(SENDER_EMAIL_DOMAIN.split('@')[0])
                server.mail(f"noreply@{SENDER_EMAIL_DOMAIN}")
                code, message = server.rcpt(email_address)
                if code == 250:
                    return True, "VALID_OR_CATCH_ALL"
                elif code == 550:
                    return False, "MAILBOX_DOES_NOT_EXIST"
                elif 400 <= code < 500:
                    return False, f"TEMPORARY_ERROR_{code}"
                else:
                    return False, f"UNKNOWN_SMTP_RESPONSE_{code}"
        except smtplib.SMTPConnectError:
            continue
        except smtplib.SMTPException:
            continue
        except socket.timeout:
            continue
        except Exception:
            continue
    return False, "NO_RELIABLE_SMTP_RESPONSE"

def is_disposable_email(email):
    domain = email.split('@')[1].lower()
    return domain in DISPOSABLE_EMAIL_DOMAINS

def validate_email_address_custom(email):
    email = email.strip().lower()
    if not is_valid_syntax(email):
        return {"email": email, "status": "invalid", "reason": "SYNTAX_INVALID"}
    if is_disposable_email(email):
        return {"email": email, "status": "risky", "reason": "DISPOSABLE_EMAIL"}
    domain = email.split('@')[1]
    mx_servers = get_mx_servers(domain)
    if not mx_servers:
        return {"email": email, "status": "invalid", "reason": "NO_MX_RECORDS"}
    smtp_exists, smtp_reason = verify_email_via_smtp(email, mx_servers)
    if smtp_exists and smtp_reason == "VALID_OR_CATCH_ALL":
        return {"email": email, "status": "valid", "reason": "SMTP_OK"}
    elif not smtp_exists and smtp_reason == "MAILBOX_DOES_NOT_EXIST":
        return {"email": email, "status": "invalid", "reason": "MAILBOX_DOES_NOT_EXIST"}
    else:
        return {"email": email, "status": "uncertain", "reason": smtp_reason}
