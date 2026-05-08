import SiteShell from "@/components/SiteShell";

export default function HomePage() {
  return (
    <SiteShell>
      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">Utah startup launchpad</p>
        <h1 id="hero-title">Navigate funding, mentors, and programs in under 2 minutes.</h1>
        <p className="hero-copy">
          GOED Founders helps you choose the right support path and move from idea to execution with local, relevant recommendations.
        </p>
        <div className="hero-actions" id="get-started">
          <a className="button button-primary" href="#how-it-works">
            Start as founder
          </a>
          <a className="button button-secondary" href="#why-goed">
            Explore startup map
          </a>
        </div>
      </section>

      <section className="panel-grid" id="how-it-works" aria-label="How it works">
        <article className="panel">
          <h2>Tell us your stage</h2>
          <p>Share what you are building, your traction, and your funding target.</p>
        </article>
        <article className="panel">
          <h2>Get matched</h2>
          <p>Receive personalized recommendations with clear rationale and links.</p>
        </article>
        <article className="panel" id="why-goed">
          <h2>Take action</h2>
          <p>Move from discovery to outreach with curated next steps built for Utah founders.</p>
        </article>
      </section>
    </SiteShell>
  );
}
