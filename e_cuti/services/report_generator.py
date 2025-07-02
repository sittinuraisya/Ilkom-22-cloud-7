import io
from datetime import datetime
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import openpyxl
from openpyxl.styles import Font, Alignment

def generate_pdf_report(cuti_data):
    """Generate PDF report using ReportLab"""
    try:
        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()

        # Create the PDF object
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title = Paragraph("Laporan Cuti Pegawai", styles['Title'])
        elements.append(title)
        
        # Add date
        date_str = datetime.now().strftime("%d %B %Y")
        date_paragraph = Paragraph(f"Tanggal: {date_str}", styles['Normal'])
        elements.append(date_paragraph)
        
        # Add some space
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # Prepare data for table
        data = [
            ["No", "Nama", "Jenis Cuti", "Tanggal Mulai", "Tanggal Selesai", "Status"]
        ]
        
        for idx, cuti in enumerate(cuti_data, 1):
            data.append([
                str(idx),
                cuti.user.full_name,
                cuti.jenis_cuti.value,
                cuti.tanggal_mulai.strftime("%d/%m/%Y"),
                cuti.tanggal_selesai.strftime("%d/%m/%Y"),
                cuti.status.value
            ])
        
        # Create table
        table = Table(data)
        
        # Add style to table
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ])
        table.setStyle(style)
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # File response
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"laporan_cuti_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        raise e

def generate_excel_report(cuti_data):
    """Generate Excel report using openpyxl"""
    try:
        # Create a workbook and add worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Laporan Cuti"
        
        # Add headers
        headers = ["No", "Nama", "Jenis Cuti", "Tanggal Mulai", "Tanggal Selesai", "Status"]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Add data
        for idx, cuti in enumerate(cuti_data, 1):
            ws.append([
                idx,
                cuti.user.full_name,
                cuti.jenis_cuti.value,
                cuti.tanggal_mulai,
                cuti.tanggal_selesai,
                cuti.status.value
            ])
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Create a file-like buffer to receive Excel data
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"laporan_cuti_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise e