"""SMTP and IMAP email operations"""

import smtplib
import imaplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config.settings import BATCH_SIZE, MAX_RETRIES, BATCH_DELAY, EMAIL_DELAY
from src.templates.report_generator import generuj_html_raport, generuj_tekst_raport
from src.utils.date_utils import get_month_name, get_month_name_without_polish_chars
from src.utils.data_utils import parse_format_type


class EmailService:
    """Service for sending emails via SMTP and IMAP"""
    
    def __init__(self, smtp_server, smtp_port, imap_server, imap_port, login, password):
        """Initialize email service with connection credentials
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            imap_server: IMAP server address
            imap_port: IMAP server port
            login: Email login
            password: Email password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.login = login
        self.password = password
        self.smtp_conn = None
        self.imap_conn = None
    
    def connect_smtp(self):
        """Connect to SMTP server
        
        Raises:
            Exception: If connection fails
        """
        self.smtp_conn = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=60)
        if self.smtp_port in [587, 465]:
            self.smtp_conn.starttls()
        self.smtp_conn.login(self.login, self.password)
    
    def connect_imap(self):
        """Connect to IMAP server
        
        Raises:
            Exception: If connection fails
        """
        self.imap_conn = imaplib.IMAP4(self.imap_server, self.imap_port)
        self.imap_conn.starttls()
        self.imap_conn.login(self.login, self.password)
        self.imap_conn.select('INBOX')
    
    def reconnect(self):
        """Reconnect to both SMTP and IMAP servers"""
        self.disconnect()
        time.sleep(2)
        self.connect_smtp()
        self.connect_imap()
    
    def disconnect(self):
        """Disconnect from both servers"""
        if self.smtp_conn:
            try:
                self.smtp_conn.quit()
            except Exception:
                pass
        if self.imap_conn:
            try:
                self.imap_conn.logout()
            except Exception:
                pass
    
    def get_imap_delimiter(self):
        """Get IMAP folder delimiter
        
        Returns:
            str: Delimiter character (usually '/' or '.')
        """
        try:
            status, delimiter_data = self.imap_conn.list('', '')
            if status == 'OK' and delimiter_data:
                for item in delimiter_data:
                    if isinstance(item, bytes):
                        item_str = item.decode('utf-8')
                        if '"/"' in item_str:
                            return '/'
                        elif '"."' in item_str:
                            return '.'
            return '/'
        except Exception:
            return '/'
    
    def send_report_email(self, sender_email, recipient_email, recipient_name, week_number, 
                         report_data, report_end_date, imap_folder="SENT.PodsumowaniaIndywidualne",
                         format_data=None, pre_table_text=None, post_table_text=None, cc_email=None):
        """Send a report email to a recipient
        
        Args:
            sender_email: Sender's email address
            recipient_email: Recipient's email address
            recipient_name: Recipient's name (promotor)
            week_number: Week number
            report_data: Dictionary of report metrics
            report_end_date: Report end date
            imap_folder: IMAP folder to save sent email to
            format_data: Dictionary of cell formats from Excel row 2 (optional)
            pre_table_text: optional custom text/html to insert before the metrics table
            post_table_text: optional custom text/html to insert after the metrics table
            cc_email: Optional CC email address (e.g., Przedstawiciel Handlowy)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        month_name = get_month_name(report_end_date)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Raport Miesięczny - {month_name} po {week_number} tygodniu"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        if cc_email:
            msg['Cc'] = cc_email
        msg['Reply-To'] = sender_email
        msg['List-Unsubscribe'] = f'<mailto:{sender_email}?subject=Unsubscribe>'
        msg['X-Mailer'] = 'SalesUp Report Generator v2.0'
        msg['X-Priority'] = '3'
        msg['X-MSMail-Priority'] = 'Normal'
        msg['Importance'] = 'Normal'
        msg['Message-ID'] = f'<{datetime.now().strftime("%Y%m%d%H%M%S")}.{hash(recipient_email)}@{sender_email.split("@")[1]}>'
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Generate HTML and text versions
        if format_data is None:
            format_data = {}
        html_content = generuj_html_raport(
            recipient_name,
            week_number,
            report_data,
            report_end_date,
            format_data=format_data,
            pre_table_text=pre_table_text,
            post_table_text=post_table_text,
        )
        text_content = generuj_tekst_raport(
            recipient_name,
            week_number,
            report_data,
            report_end_date,
            format_data=format_data,
            pre_table_text=pre_table_text,
            post_table_text=post_table_text,
        )
        
        # Attach content
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # Determine recipients (To + Cc)
        recipients = [recipient_email]
        if cc_email:
            recipients.append(cc_email)

        # Send with retries
        for attempt in range(MAX_RETRIES):
            try:
                self.smtp_conn.send_message(msg, to_addrs=recipients)
                
                # Save to IMAP folder
                try:
                    self._save_to_imap(imap_folder, msg)
                except Exception as e:
                    print(f"Błąd zapisywania w IMAP dla {recipient_email}: {e}")
                
                return True
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Błąd wysyłania do {recipient_email}: {e}")
                    return False
        
        return False
    
    def _save_to_imap(self, folder_name, message):
        """Save message to IMAP folder
        
        Args:
            folder_name: Name of the folder
            message: MIMEMultipart message object
        """
        try:
            self.imap_conn.select(folder_name)
        except imaplib.IMAP4.error:
            # Folder doesn't exist, create it
            self.imap_conn.create(folder_name)
            self.imap_conn.select(folder_name)
        
        # Append message to folder
        self.imap_conn.append(folder_name, None, None, message.as_string().encode('utf-8'))
