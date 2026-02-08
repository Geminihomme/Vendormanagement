/**
 * REPORTS PAGE
 *
 * WHAT THIS PAGE DOES:
 * This is your "print shop" — a central place to generate and download
 * business reports. Think of it like going to a copy center:
 * - You pick WHAT kind of report you want (vendors, contracts, spending, risk)
 * - You pick WHAT FORMAT you want (CSV for data, Excel for formatted reports)
 * - You click "Download" and the file appears on your computer
 *
 * TWO FORMAT TYPES:
 *
 * CSV (Comma-Separated Values):
 *   - Simple text file with data separated by commas
 *   - Like a plain spreadsheet with no formatting
 *   - Opens in Excel, Google Sheets, or even Notepad
 *   - Best for: importing data into other tools, quick data dumps
 *   - Example: "Acme Corp,Technology,Active,2024-01-15"
 *
 * Excel (.xlsx):
 *   - Rich formatted workbook with multiple sheets
 *   - Has colors, bold headers, auto-sized columns
 *   - Best for: presenting to management, printing, detailed analysis
 *   - Example: A spend report with Summary sheet + Vendor Details sheet + Monthly Trend sheet
 *
 * WHEN TO USE WHICH:
 *   - Need raw data to import somewhere? → CSV
 *   - Need a polished report for a meeting? → Excel
 *   - Need to email a quick update? → CSV (smaller file)
 *   - Need multi-tab analysis? → Excel (supports multiple sheets)
 */

import React, { useState } from 'react';
import {
  downloadVendorsCSV,
  downloadContractsCSV,
  downloadPaymentsCSV,
  downloadSpendReportExcel,
  downloadExpiryReportExcel,
  downloadRiskReportExcel,
} from '../services/api';

/**
 * Each report "card" on the page is described by this shape.
 * It's like a menu item at a restaurant — name, description, and what happens when you order it.
 */
interface ReportCard {
  title: string;
  description: string;
  format: 'CSV' | 'Excel';
  icon: string;          // A visual label for the format type
  downloadFn: () => Promise<void>;
}

function ReportsPage() {
  // Track which report is currently downloading (so we can show a spinner)
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  /**
   * Handle the download button click.
   * This wraps every download in loading/error handling so each card
   * doesn't need to repeat the same logic.
   */
  const handleDownload = async (report: ReportCard) => {
    setDownloading(report.title);
    setError(null);
    setSuccessMsg(null);

    try {
      await report.downloadFn();
      setSuccessMsg(`${report.title} downloaded successfully!`);
    } catch (err: any) {
      console.error('Download failed:', err);
      setError(`Failed to download ${report.title}. Please try again.`);
    } finally {
      setDownloading(null);
    }
  };

  // All available reports, organized into two groups
  const csvReports: ReportCard[] = [
    {
      title: 'Vendors CSV',
      description: 'All vendors with their status, category, contact info, and creation date. Great for importing into other systems.',
      format: 'CSV',
      icon: 'CSV',
      downloadFn: downloadVendorsCSV,
    },
    {
      title: 'Contracts CSV',
      description: 'Every contract with vendor name, dates, value, status, and document links. Useful for auditing.',
      format: 'CSV',
      icon: 'CSV',
      downloadFn: downloadContractsCSV,
    },
    {
      title: 'Payments CSV',
      description: 'Complete payment history — vendor, amount, date, status, and method. Perfect for accounting imports.',
      format: 'CSV',
      icon: 'CSV',
      downloadFn: downloadPaymentsCSV,
    },
  ];

  const excelReports: ReportCard[] = [
    {
      title: 'Spend Report',
      description: 'Multi-sheet workbook: Summary stats, spend broken down by vendor, monthly spending trends, and full payment details.',
      format: 'Excel',
      icon: 'XLSX',
      downloadFn: downloadSpendReportExcel,
    },
    {
      title: 'Contract Expiry Report',
      description: 'Contracts expiring in the next 90 days (color-coded by urgency) plus a full contract listing. Great for renewal planning.',
      format: 'Excel',
      icon: 'XLSX',
      downloadFn: downloadExpiryReportExcel,
    },
    {
      title: 'Risk Assessment Report',
      description: 'Risk level summary, detailed scores for every vendor, and individual factor breakdowns. Perfect for compliance reviews.',
      format: 'Excel',
      icon: 'XLSX',
      downloadFn: downloadRiskReportExcel,
    },
  ];

  return (
    <div className="container">
      <div className="page-header">
        <h1>Reports & Exports</h1>
        <p className="page-subtitle">
          Download your vendor data as reports. CSV files are simple data exports;
          Excel files are formatted reports with multiple sheets.
        </p>
      </div>

      {/* Status messages */}
      {error && <div className="alert alert-danger">{error}</div>}
      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      {/* CSV SECTION — Quick Data Exports */}
      <section className="report-section">
        <h2 className="report-section-title">
          <span className="report-format-badge csv">CSV</span>
          Quick Data Exports
        </h2>
        <p className="report-section-desc">
          Simple data files that open in any spreadsheet app. Best for raw data and importing into other tools.
        </p>
        <div className="report-grid">
          {csvReports.map((report) => (
            <div key={report.title} className="report-card">
              <div className="report-card-header">
                <span className="report-icon csv">{report.icon}</span>
                <h3>{report.title}</h3>
              </div>
              <p className="report-card-desc">{report.description}</p>
              <button
                className="btn btn-secondary report-download-btn"
                onClick={() => handleDownload(report)}
                disabled={downloading !== null}
              >
                {downloading === report.title ? 'Downloading...' : 'Download CSV'}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* EXCEL SECTION — Formatted Business Reports */}
      <section className="report-section">
        <h2 className="report-section-title">
          <span className="report-format-badge excel">Excel</span>
          Formatted Business Reports
        </h2>
        <p className="report-section-desc">
          Professional multi-sheet workbooks with styled headers, color-coded data, and auto-sized columns.
          Best for meetings, compliance reviews, and management presentations.
        </p>
        <div className="report-grid">
          {excelReports.map((report) => (
            <div key={report.title} className="report-card report-card-excel">
              <div className="report-card-header">
                <span className="report-icon excel">{report.icon}</span>
                <h3>{report.title}</h3>
              </div>
              <p className="report-card-desc">{report.description}</p>
              <button
                className="btn btn-primary report-download-btn"
                onClick={() => handleDownload(report)}
                disabled={downloading !== null}
              >
                {downloading === report.title ? 'Generating...' : 'Download Excel'}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* HELP SECTION — When to use which format */}
      <section className="report-section report-help">
        <h2 className="report-section-title">Which format should I use?</h2>
        <div className="report-help-grid">
          <div className="report-help-card">
            <h4>Use CSV when...</h4>
            <ul>
              <li>You need to import data into another system</li>
              <li>You want a quick, lightweight file</li>
              <li>You need to email a small dataset</li>
              <li>You plan to do your own analysis in Google Sheets</li>
            </ul>
          </div>
          <div className="report-help-card">
            <h4>Use Excel when...</h4>
            <ul>
              <li>You need a polished report for a meeting</li>
              <li>You want color-coded urgency indicators</li>
              <li>You need multiple data views in one file</li>
              <li>You're preparing for a compliance audit</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

export default ReportsPage;
