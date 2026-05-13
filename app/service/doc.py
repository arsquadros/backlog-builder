from weasyprint import HTML

from app.service.ai import AIService
from app.static.styles import STYLES_REPORT


class DocService:
    @staticmethod
    def generate_doc_report(project_name, data):
        html_content = f"""
        <html>
            <head>
                {STYLES_REPORT}
            </head>
            <body>
                <h1>Documentação de Requisitos: {project_name}</h1>
        """
        
        for ep in data:
            for ft in ep.get('children', []):
                for bk in ft.get('children', []):
                    desc = AIService.generate_pbi_description(ep['title'], ft['title'], bk['title'], bk.get('children', []))
                    html_content += f"""
                    <div class='pbi-card'>
                        <div class='pbi-header'><strong>ITEM: {bk['title']}</strong> (Ref: {ft['title']})</div>
                        <div class='context-box'>{desc.replace(chr(10), '<br>')}</div>
                        <div class='tasks'><strong>Tarefas relacionadas:</strong> {", ".join([t['title'] for t in bk.get('children', [])])}</div>
                    </div>
                    """
        
        html_content += "</body></html>"
        return HTML(string=html_content).write_pdf()