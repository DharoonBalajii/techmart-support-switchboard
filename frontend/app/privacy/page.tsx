import Link from "next/link";
import "../landing.css"; // Reuse landing page styles for consistency

export default function PrivacyPolicy() {
  return (
    <div className="lp">
      <nav className="lp-nav">
        <Link href="/" className="lp-brand">
          <div className="brand-mark" aria-hidden>
            <span /><span /><span />
            <div className="brand-core" />
          </div>
          <b>Support Switchboard</b>
        </Link>
      </nav>
      
      <main className="lp-section" style={{ paddingTop: "120px", maxWidth: "800px", margin: "0 auto", textAlign: "left" }}>
        <h1>Privacy Policy</h1>
        <div style={{ marginTop: "32px", display: "flex", flexDirection: "column", gap: "16px", color: "var(--text-sub)" }}>
          <p>Last updated: {new Date().toLocaleDateString()}</p>
          <p>
            Welcome to TechMart Support Switchboard. We are committed to protecting your personal information and your right to privacy.
            If you have any questions or concerns about this privacy notice, or our practices with regards to your personal information, please contact us.
          </p>
          <h2>1. Information We Collect</h2>
          <p>
            We collect personal information that you voluntarily provide to us when you register on the website, express an interest in obtaining information about us or our products and services, when you participate in activities on the website, or otherwise when you contact us.
          </p>
          <h2>2. How We Use Your Information</h2>
          <p>
            We use personal information collected via our website for a variety of business purposes described below. We process your personal information for these purposes in reliance on our legitimate business interests, in order to enter into or perform a contract with you, with your consent, and/or for compliance with our legal obligations.
          </p>
          <h2>3. Sharing Your Information</h2>
          <p>
            We only share information with your consent, to comply with laws, to provide you with services, to protect your rights, or to fulfill business obligations.
          </p>
        </div>
      </main>

      <footer className="lp-foot">
        <span>TechMart Electronics · Support Switchboard</span>
        <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
          <Link href="/privacy">Privacy Policy</Link>
          <Link href="/terms">Terms & Conditions</Link>
        </div>
      </footer>
    </div>
  );
}
