import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BrandLogo } from "../components/BrandLogo";
import { APP_ROUTES } from "../routes/config";

const CONTACT_EMAIL = "antonioriccardi92@hotmail.it";

export function PrivacyPolicyPage() {
  return (
    <div className="gcr-login">
      <motion.article
        className="gcr-legal"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <header className="gcr-legal__header">
          <div className="gcr-login__logo">
            <BrandLogo variant="mark" size="md" />
          </div>
          <p className="gcr-legal__brand">Growth Control Room</p>
          <h1 className="gcr-legal__title">Privacy Policy</h1>
          <p className="gcr-legal__updated">Last updated: June 10, 2026</p>
        </header>

        <p className="gcr-legal__intro">
          Growth Control Room helps merchants analyze store performance and plan SEO blog content
          using data made available through authorized store integrations.
        </p>

        <section className="gcr-legal__section">
          <h2>Data we access</h2>
          <p>
            When a merchant connects their store, Growth Control Room may access order data,
            product data, store information, and content data such as blogs, articles, pages, and
            related metadata. This data is used only to provide dashboards, insights, reporting,
            synchronization, and content planning features.
          </p>
        </section>

        <section className="gcr-legal__section">
          <h2>How we use data</h2>
          <p>
            We use store data to display analytics, identify performance trends, support content
            planning workflows, and help merchants create or manage SEO blog content. Growth Control
            Room does not scrape data from stores and does not modify orders, payments,
            fulfillments, or checkout information.
          </p>
        </section>

        <section className="gcr-legal__section">
          <h2>Content permissions</h2>
          <p>
            If the merchant grants content permissions, Growth Control Room may read and write
            blog-related content only to support editorial planning, draft creation, and content
            publishing workflows requested by the merchant.
          </p>
        </section>

        <section className="gcr-legal__section">
          <h2>Data sharing</h2>
          <p>
            We do not sell merchant data. We do not share merchant data with advertisers. Data may
            be processed by infrastructure and service providers used to operate the application,
            such as hosting, database, and AI service providers, only for the purpose of delivering
            the app functionality.
          </p>
        </section>

        <section className="gcr-legal__section">
          <h2>Data storage and security</h2>
          <p>
            Access tokens and integration credentials are stored securely and are not shown
            publicly. We use reasonable technical and organizational measures to protect merchant
            data from unauthorized access.
          </p>
        </section>

        <section className="gcr-legal__section">
          <h2>Data retention and deletion</h2>
          <p>
            Merchants may disconnect their store integration at any time. Upon request, we can delete
            stored integration data and related records associated with the merchant account, unless
            retention is required for security, legal, or operational reasons.
          </p>
        </section>

        <section className="gcr-legal__section">
          <h2>Contact</h2>
          <p>
            For privacy questions or data deletion requests, contact:{" "}
            <a className="gcr-legal__link" href={`mailto:${CONTACT_EMAIL}`}>
              {CONTACT_EMAIL}
            </a>
          </p>
        </section>

        <footer className="gcr-legal__footer">
          <Link className="gcr-legal__link" to={APP_ROUTES.login}>
            Back to Growth Control Room
          </Link>
        </footer>
      </motion.article>
    </div>
  );
}
