import Link from "next/link";
import "../landing.css"; // Reuse landing page styles for consistency

export default function TermsAndConditions() {
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
        <h1>Terms & Conditions</h1>
        <div style={{ marginTop: "32px", display: "flex", flexDirection: "column", gap: "16px", color: "var(--text-sub)" }}>
          <p>Last updated: {new Date().toLocaleDateString()}</p>
          <p>
            Please read these terms and conditions carefully before using Our Service.
          </p>
          <h2>1. Agreement to Terms</h2>
          <p>
            By accessing or using the Service, you agree to be bound by these Terms. If you disagree with any part of the terms then you may not access the Service.
          </p>
          <h2>2. Intellectual Property</h2>
          <p>
            The Service and its original content, features and functionality are and will remain the exclusive property of TechMart and its licensors.
          </p>
          <h2>3. Termination</h2>
          <p>
            We may terminate or suspend access to our Service immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms.
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
