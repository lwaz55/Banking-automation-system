const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/v1";

let cachedToken: string | null = null;

async function getToken() {
  if (cachedToken) return cachedToken;
  
  const formData = new URLSearchParams();
  formData.append("username", "admin");
  formData.append("password", "admin"); // Password doesn't matter for MVP
  
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString()
  });
  
  if (!res.ok) {
    console.warn("Auto-login failed, proceeding without token");
    return "";
  }
  
  const data = await res.json();
  cachedToken = data.access_token;
  return cachedToken;
}

async function getHeaders() {
  const token = await getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {})
  };
}

export async function fetchTickets() {
  const res = await fetch(`${API_BASE}/tickets/`);
  if (!res.ok) throw new Error("Failed to fetch tickets");
  return res.json();
}

export async function fetchTicket(id: string) {
  const res = await fetch(`${API_BASE}/tickets/${id}`);
  if (!res.ok) throw new Error("Failed to fetch ticket");
  return res.json();
}

export async function fetchReports(ticketId: string) {
  const res = await fetch(`${API_BASE}/reports/ticket/${ticketId}`);
  if (!res.ok) throw new Error("Failed to fetch reports");
  return res.json();
}

export async function submitEvent(payload: any) {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/inputs/`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit event");
  return res.json();
}

export async function validateReport(reportId: number, actionTaken: string) {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/reports/${reportId}/validate`, {
    method: "POST",
    headers,
    body: JSON.stringify({ action_taken: actionTaken }),
  });
  if (!res.ok) throw new Error("Failed to validate report");
  return res.json();
}

export async function invalidateReport(reportId: number) {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/reports/${reportId}/invalidate`, {
    method: "POST",
    headers: { ...(headers["Authorization"] ? { "Authorization": headers["Authorization"] } : {}) }
  });
  if (!res.ok) throw new Error("Failed to invalidate report");
  return res.json();
}

export async function modifyReport(reportId: number, content: any) {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/reports/${reportId}/modify`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error("Failed to modify report");
  return res.json();
}

export async function fetchAuditLog(params?: { ticket_id?: string; dept_id?: string }) {
  const url = new URL(`${API_BASE}/audit/`);
  if (params?.ticket_id) url.searchParams.append("ticket_id", params.ticket_id);
  if (params?.dept_id) url.searchParams.append("dept_id", params.dept_id);
  
  const headers = await getHeaders();
  const res = await fetch(url.toString(), {
    headers: { ...(headers["Authorization"] ? { "Authorization": headers["Authorization"] } : {}) }
  });
  if (!res.ok) throw new Error("Failed to fetch audit log");
  return res.json();
}
export async function fetchCustomerProfile(customerId: string) {
  const res = await fetch(`${API_BASE}/customers/${encodeURIComponent(customerId)}`);
  if (!res.ok) throw new Error("Failed to fetch customer profile");
  return res.json();
}

export async function exportTicketPDF(ticketId: string) {
  const headers = await getHeaders();

  const res = await fetch(`${API_BASE}/reports/ticket/${ticketId}/export/pdf`, {
    method: "GET",
    headers,
    cache: "no-store"
  });

  if (!res.ok) {
    const errorText = await res.text();
    alert(`Export failed (${res.status}): ${errorText}`);
    return;
  }

  // Read raw bytes and force the MIME type to application/pdf.
  // This is the critical fix: without specifying the type the browser
  // creates a generic "octet-stream" blob and the filename loses its
  // .pdf extension.
  const rawBlob = await res.blob();
  const pdfBlob = new Blob([rawBlob], { type: "application/pdf" });

  const url = window.URL.createObjectURL(pdfBlob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = `sentinels_report_ticket_${ticketId}.pdf`;
  document.body.appendChild(a);
  a.click();

  setTimeout(() => {
    window.URL.revokeObjectURL(url);
    if (document.body.contains(a)) document.body.removeChild(a);
  }, 200);
}

export async function chatWithCopilot(ticketId: string | number, message: string) {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}/chat/ticket/${ticketId}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to chat with Copilot");
  return res.json();
}

