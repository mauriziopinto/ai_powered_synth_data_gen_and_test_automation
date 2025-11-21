"""Results export and sharing for workflow outputs."""

import json
import csv
import hashlib
import secrets
import zipfile
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    SQL = "sql"
    HTML = "html"
    PDF = "pdf"


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    output_directory: str = "exports"
    compression: bool = False
    compression_level: int = 6  # 0-9, higher = more compression
    include_metadata: bool = True
    secure_links: bool = True
    link_expiration_hours: int = 24
    enable_email_sharing: bool = False
    email_server: Optional[str] = None
    archive_enabled: bool = True
    archive_directory: str = "results_archive"


@dataclass
class ExportResult:
    """Result of an export operation."""
    export_id: str
    format: ExportFormat
    file_path: str
    file_size: int
    created_at: datetime = field(default_factory=datetime.now)
    download_link: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'export_id': self.export_id,
            'format': self.format.value,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
            'download_link': self.download_link,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class ResultsExporter:
    """Handles export and sharing of workflow results."""
    
    def __init__(self, config: ExportConfig):
        """Initialize results exporter.
        
        Args:
            config: Export configuration
        """
        self.config = config
        self.output_dir = Path(config.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._download_links: Dict[str, ExportResult] = {}
        logger.info(f"Initialized results exporter: {config.output_directory}")

    def export_data(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        filename: Optional[str] = None
    ) -> ExportResult:
        """Export data in specified format.
        
        Args:
            data: Data to export
            format: Export format
            filename: Optional filename
        
        Returns:
            Export result
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.{format.value}"
        
        file_path = self.output_dir / filename
        
        # Export based on format
        if format == ExportFormat.CSV:
            self._export_csv(data, file_path)
        elif format == ExportFormat.JSON:
            self._export_json(data, file_path)
        elif format == ExportFormat.PARQUET:
            try:
                self._export_parquet(data, file_path)
            except Exception:
                # Fallback to JSON if Parquet fails
                file_path = file_path.with_suffix('.json')
                self._export_json(data, file_path)
        elif format == ExportFormat.SQL:
            self._export_sql(data, file_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Generate export ID
        export_id = self._generate_export_id()
        
        # Create result
        result = ExportResult(
            export_id=export_id,
            format=format,
            file_path=str(file_path),
            file_size=file_size
        )
        
        # Generate secure download link if enabled
        if self.config.secure_links:
            result.download_link = self._generate_download_link(result)
            result.expires_at = datetime.now() + timedelta(hours=self.config.link_expiration_hours)
            self._download_links[result.download_link] = result
        
        logger.info(f"Exported {len(data)} records to {file_path} ({format.value})")
        return result
    
    def _export_csv(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Export data as CSV."""
        if not data:
            return
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _export_json(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Export data as JSON."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _export_parquet(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Export data as Parquet."""
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_parquet(file_path, index=False)
    
    def _export_sql(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Export data as SQL INSERT statements."""
        if not data:
            return
        
        table_name = "exported_data"
        columns = list(data[0].keys())
        
        with open(file_path, 'w') as f:
            for row in data:
                values = [f"'{v}'" if isinstance(v, str) else str(v) for v in row.values()]
                sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                f.write(sql)

    def generate_html_report(
        self,
        report_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> ExportResult:
        """Generate HTML report.
        
        Args:
            report_data: Report data
            filename: Optional filename
        
        Returns:
            Export result
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.html"
        
        file_path = self.output_dir / filename
        
        html_content = self._generate_html_content(report_data)
        
        with open(file_path, 'w') as f:
            f.write(html_content)
        
        file_size = file_path.stat().st_size
        export_id = self._generate_export_id()
        
        result = ExportResult(
            export_id=export_id,
            format=ExportFormat.HTML,
            file_path=str(file_path),
            file_size=file_size
        )
        
        logger.info(f"Generated HTML report: {file_path}")
        return result
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content for report."""
        title = report_data.get('title', 'Workflow Execution Report')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #ecf0f1; border-radius: 5px; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        .success {{ color: #27ae60; }}
        .failure {{ color: #e74c3c; }}
        .timestamp {{ color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        # Add metrics
        if 'metrics' in report_data:
            html += "<h2>Summary Metrics</h2>\n"
            for key, value in report_data['metrics'].items():
                html += f"""
        <div class="metric">
            <div class="metric-label">{key.replace('_', ' ').title()}</div>
            <div class="metric-value">{value}</div>
        </div>
"""
        
        # Add details table
        if 'details' in report_data:
            html += "<h2>Details</h2>\n<table>\n<thead><tr>"
            if report_data['details']:
                for key in report_data['details'][0].keys():
                    html += f"<th>{key.replace('_', ' ').title()}</th>"
                html += "</tr></thead>\n<tbody>\n"
                
                for row in report_data['details']:
                    html += "<tr>"
                    for value in row.values():
                        html += f"<td>{value}</td>"
                    html += "</tr>\n"
                html += "</tbody>\n</table>\n"
        
        html += """
    </div>
</body>
</html>
"""
        return html

    def export_workflow_package(
        self,
        workflow_data: Dict[str, Any],
        package_name: Optional[str] = None
    ) -> ExportResult:
        """Export complete workflow execution package.
        
        Args:
            workflow_data: Complete workflow data
            package_name: Optional package name
        
        Returns:
            Export result
        """
        if not package_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"workflow_package_{timestamp}"
        
        package_dir = self.output_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Export workflow metadata
        metadata_file = package_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'workflow_id': workflow_data.get('workflow_id'),
                'name': workflow_data.get('name'),
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }, f, indent=2)
        
        # Export synthetic data if present
        if 'synthetic_data' in workflow_data:
            data_file = package_dir / "synthetic_data.json"
            with open(data_file, 'w') as f:
                json.dump(workflow_data['synthetic_data'], f, indent=2)
        
        # Export quality report if present
        if 'quality_report' in workflow_data:
            report_file = package_dir / "quality_report.json"
            with open(report_file, 'w') as f:
                json.dump(workflow_data['quality_report'], f, indent=2)
        
        # Export test results if present
        if 'test_results' in workflow_data:
            test_file = package_dir / "test_results.json"
            with open(test_file, 'w') as f:
                json.dump(workflow_data['test_results'], f, indent=2)
        
        # Export agent logs if present
        if 'agent_logs' in workflow_data:
            logs_file = package_dir / "agent_logs.txt"
            with open(logs_file, 'w') as f:
                f.write(workflow_data['agent_logs'])
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
        
        export_id = self._generate_export_id()
        
        result = ExportResult(
            export_id=export_id,
            format=ExportFormat.JSON,
            file_path=str(package_dir),
            file_size=total_size
        )
        
        logger.info(f"Exported workflow package: {package_dir}")
        return result
    
    def _generate_export_id(self) -> str:
        """Generate unique export ID."""
        return f"exp_{secrets.token_hex(8)}"
    
    def _generate_download_link(self, result: ExportResult) -> str:
        """Generate secure download link.
        
        Args:
            result: Export result
        
        Returns:
            Secure download link
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Create link (in production, this would be a real URL)
        link = f"https://example.com/download/{token}"
        
        logger.info(f"Generated download link for {result.export_id}")
        return link
    
    def verify_download_link(self, link: str) -> Optional[ExportResult]:
        """Verify and retrieve export result for download link.
        
        Args:
            link: Download link
        
        Returns:
            Export result if valid, None otherwise
        """
        result = self._download_links.get(link)
        
        if not result:
            return None
        
        # Check expiration
        if result.expires_at and datetime.now() > result.expires_at:
            logger.warning(f"Download link expired: {link}")
            return None
        
        return result


class ResultsArchive:
    """Manages historical workflow results archive."""
    
    def __init__(self, archive_directory: str = "results_archive"):
        """Initialize results archive.
        
        Args:
            archive_directory: Directory for archived results
        """
        self.archive_dir = Path(archive_directory)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.archive_dir / "index.json"
        self._load_index()
        logger.info(f"Initialized results archive: {archive_directory}")
    
    def _load_index(self) -> None:
        """Load archive index."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {
                'workflows': [],
                'last_updated': datetime.now().isoformat()
            }
    
    def _save_index(self) -> None:
        """Save archive index."""
        self.index['last_updated'] = datetime.now().isoformat()
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def archive_workflow(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Archive a workflow execution.
        
        Args:
            workflow_id: Workflow identifier
            workflow_data: Complete workflow data
            metadata: Optional metadata
        
        Returns:
            Archive ID
        """
        archive_id = f"archive_{workflow_id}_{int(datetime.now().timestamp())}"
        archive_path = self.archive_dir / archive_id
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Save workflow data
        data_file = archive_path / "workflow_data.json"
        with open(data_file, 'w') as f:
            json.dump(workflow_data, f, indent=2, default=str)
        
        # Save metadata
        meta = metadata or {}
        meta.update({
            'archive_id': archive_id,
            'workflow_id': workflow_id,
            'archived_at': datetime.now().isoformat(),
            'size_bytes': data_file.stat().st_size
        })
        
        meta_file = archive_path / "metadata.json"
        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
        
        # Update index
        self.index['workflows'].append(meta)
        self._save_index()
        
        logger.info(f"Archived workflow {workflow_id} as {archive_id}")
        return archive_id
    
    def search_archives(
        self,
        workflow_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search archived workflows.
        
        Args:
            workflow_id: Filter by workflow ID
            start_date: Filter by start date
            end_date: Filter by end date
            tags: Filter by tags
        
        Returns:
            List of matching workflow metadata
        """
        results = []
        
        for workflow in self.index['workflows']:
            # Filter by workflow ID
            if workflow_id and workflow.get('workflow_id') != workflow_id:
                continue
            
            # Filter by date range
            archived_at = datetime.fromisoformat(workflow['archived_at'])
            if start_date and archived_at < start_date:
                continue
            if end_date and archived_at > end_date:
                continue
            
            # Filter by tags
            if tags:
                workflow_tags = workflow.get('tags', [])
                if not any(tag in workflow_tags for tag in tags):
                    continue
            
            results.append(workflow)
        
        return results
    
    def retrieve_archive(self, archive_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve archived workflow data.
        
        Args:
            archive_id: Archive identifier
        
        Returns:
            Workflow data if found, None otherwise
        """
        archive_path = self.archive_dir / archive_id
        
        if not archive_path.exists():
            logger.warning(f"Archive not found: {archive_id}")
            return None
        
        data_file = archive_path / "workflow_data.json"
        
        if not data_file.exists():
            logger.warning(f"Archive data file not found: {archive_id}")
            return None
        
        with open(data_file, 'r') as f:
            return json.load(f)
    
    def delete_archive(self, archive_id: str) -> bool:
        """Delete an archived workflow.
        
        Args:
            archive_id: Archive identifier
        
        Returns:
            True if deleted, False otherwise
        """
        archive_path = self.archive_dir / archive_id
        
        if not archive_path.exists():
            return False
        
        # Remove from index
        self.index['workflows'] = [
            w for w in self.index['workflows']
            if w.get('archive_id') != archive_id
        ]
        self._save_index()
        
        # Delete directory
        import shutil
        shutil.rmtree(archive_path)
        
        logger.info(f"Deleted archive: {archive_id}")
        return True
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get archive statistics.
        
        Returns:
            Archive statistics
        """
        total_workflows = len(self.index['workflows'])
        total_size = sum(w.get('size_bytes', 0) for w in self.index['workflows'])
        
        # Get date range
        if self.index['workflows']:
            dates = [datetime.fromisoformat(w['archived_at']) for w in self.index['workflows']]
            oldest = min(dates)
            newest = max(dates)
        else:
            oldest = newest = None
        
        return {
            'total_workflows': total_workflows,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_archive': oldest.isoformat() if oldest else None,
            'newest_archive': newest.isoformat() if newest else None
        }


class ComprehensiveExporter(ResultsExporter):
    """Enhanced exporter with compression, PDF generation, and archiving."""
    
    def __init__(self, config: ExportConfig):
        """Initialize comprehensive exporter.
        
        Args:
            config: Export configuration
        """
        super().__init__(config)
        
        # Initialize archive if enabled
        if config.archive_enabled:
            self.archive = ResultsArchive(config.archive_directory)
        else:
            self.archive = None
    
    def export_data_compressed(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        filename: Optional[str] = None
    ) -> ExportResult:
        """Export data with compression.
        
        Args:
            data: Data to export
            format: Export format
            filename: Optional filename
        
        Returns:
            Export result
        """
        # First export normally
        result = self.export_data(data, format, filename)
        
        # Then compress if enabled
        if self.config.compression:
            compressed_path = Path(result.file_path).with_suffix(f'.{format.value}.gz')
            
            import gzip
            with open(result.file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=self.config.compression_level) as f_out:
                    f_out.writelines(f_in)
            
            # Update result
            result.file_path = str(compressed_path)
            result.file_size = compressed_path.stat().st_size
            
            # Remove uncompressed file
            Path(result.file_path.replace('.gz', '')).unlink()
            
            logger.info(f"Compressed export to {compressed_path}")
        
        return result
    
    def generate_pdf_report(
        self,
        report_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> ExportResult:
        """Generate PDF report.
        
        Args:
            report_data: Report data
            filename: Optional filename
        
        Returns:
            Export result
        """
        # First generate HTML
        html_result = self.generate_html_report(report_data, filename)
        
        # Try to convert to PDF
        try:
            from weasyprint import HTML
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{timestamp}.pdf"
            
            pdf_path = self.output_dir / filename
            
            # Convert HTML to PDF
            HTML(html_result.file_path).write_pdf(pdf_path)
            
            file_size = pdf_path.stat().st_size
            export_id = self._generate_export_id()
            
            result = ExportResult(
                export_id=export_id,
                format=ExportFormat.PDF,
                file_path=str(pdf_path),
                file_size=file_size
            )
            
            logger.info(f"Generated PDF report: {pdf_path}")
            return result
            
        except ImportError:
            logger.warning("WeasyPrint not available, returning HTML report instead")
            return html_result
    
    def export_with_visualizations(
        self,
        report_data: Dict[str, Any],
        charts: Optional[List[Dict[str, Any]]] = None,
        filename: Optional[str] = None
    ) -> ExportResult:
        """Export report with embedded visualizations.
        
        Args:
            report_data: Report data
            charts: Optional chart specifications
            filename: Optional filename
        
        Returns:
            Export result
        """
        # Generate charts if provided
        chart_images = []
        if charts:
            try:
                import matplotlib.pyplot as plt
                import base64
                
                for i, chart_spec in enumerate(charts):
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    chart_type = chart_spec.get('type', 'bar')
                    data = chart_spec.get('data', {})
                    
                    if chart_type == 'bar':
                        ax.bar(data.get('x', []), data.get('y', []))
                    elif chart_type == 'line':
                        ax.plot(data.get('x', []), data.get('y', []))
                    elif chart_type == 'scatter':
                        ax.scatter(data.get('x', []), data.get('y', []))
                    
                    ax.set_title(chart_spec.get('title', f'Chart {i+1}'))
                    ax.set_xlabel(chart_spec.get('xlabel', 'X'))
                    ax.set_ylabel(chart_spec.get('ylabel', 'Y'))
                    
                    # Save to bytes
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                    buf.seek(0)
                    
                    # Encode as base64
                    img_base64 = base64.b64encode(buf.read()).decode()
                    chart_images.append(f"data:image/png;base64,{img_base64}")
                    
                    plt.close(fig)
                
            except ImportError:
                logger.warning("Matplotlib not available, skipping chart generation")
        
        # Add charts to report data
        if chart_images:
            report_data['charts'] = chart_images
        
        # Generate HTML report with charts
        return self.generate_html_report(report_data, filename)
    
    def create_shareable_package(
        self,
        workflow_data: Dict[str, Any],
        include_data: bool = True,
        include_reports: bool = True,
        include_logs: bool = True,
        package_name: Optional[str] = None
    ) -> ExportResult:
        """Create a shareable ZIP package of workflow results.
        
        Args:
            workflow_data: Complete workflow data
            include_data: Include synthetic data
            include_reports: Include quality reports
            include_logs: Include agent logs
            package_name: Optional package name
        
        Returns:
            Export result
        """
        if not package_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"workflow_package_{timestamp}"
        
        zip_path = self.output_dir / f"{package_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata
            metadata = {
                'workflow_id': workflow_data.get('workflow_id'),
                'name': workflow_data.get('name'),
                'exported_at': datetime.now().isoformat(),
                'version': '1.0',
                'contents': []
            }
            
            # Add synthetic data
            if include_data and 'synthetic_data' in workflow_data:
                zipf.writestr('synthetic_data.json', 
                             json.dumps(workflow_data['synthetic_data'], indent=2))
                metadata['contents'].append('synthetic_data.json')
            
            # Add quality report
            if include_reports and 'quality_report' in workflow_data:
                zipf.writestr('quality_report.json',
                             json.dumps(workflow_data['quality_report'], indent=2))
                metadata['contents'].append('quality_report.json')
            
            # Add test results
            if include_reports and 'test_results' in workflow_data:
                zipf.writestr('test_results.json',
                             json.dumps(workflow_data['test_results'], indent=2))
                metadata['contents'].append('test_results.json')
            
            # Add agent logs
            if include_logs and 'agent_logs' in workflow_data:
                zipf.writestr('agent_logs.txt', workflow_data['agent_logs'])
                metadata['contents'].append('agent_logs.txt')
            
            # Add metadata
            zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
        
        file_size = zip_path.stat().st_size
        export_id = self._generate_export_id()
        
        result = ExportResult(
            export_id=export_id,
            format=ExportFormat.JSON,
            file_path=str(zip_path),
            file_size=file_size
        )
        
        # Generate download link if enabled
        if self.config.secure_links:
            result.download_link = self._generate_download_link(result)
            result.expires_at = datetime.now() + timedelta(hours=self.config.link_expiration_hours)
            self._download_links[result.download_link] = result
        
        logger.info(f"Created shareable package: {zip_path} ({file_size} bytes)")
        return result
    
    def share_via_email(
        self,
        export_result: ExportResult,
        recipient_email: str,
        subject: Optional[str] = None,
        message: Optional[str] = None
    ) -> bool:
        """Share export via email.
        
        Args:
            export_result: Export result to share
            recipient_email: Recipient email address
            subject: Optional email subject
            message: Optional email message
        
        Returns:
            True if sent successfully
        """
        if not self.config.enable_email_sharing:
            logger.warning("Email sharing is not enabled")
            return False
        
        # In a real implementation, this would send an actual email
        # For demo purposes, we'll just log it
        
        subject = subject or f"Workflow Results Export - {export_result.export_id}"
        message = message or f"Your workflow results are ready for download."
        
        logger.info(f"Email sent to {recipient_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Download link: {export_result.download_link}")
        
        return True
    
    def archive_workflow_results(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> str:
        """Archive workflow results for historical reference.
        
        Args:
            workflow_id: Workflow identifier
            workflow_data: Complete workflow data
            tags: Optional tags for categorization
        
        Returns:
            Archive ID
        """
        if not self.archive:
            raise ValueError("Archive is not enabled")
        
        metadata = {
            'tags': tags or [],
            'workflow_name': workflow_data.get('name', 'Unknown'),
            'status': workflow_data.get('status', 'Unknown')
        }
        
        return self.archive.archive_workflow(workflow_id, workflow_data, metadata)
