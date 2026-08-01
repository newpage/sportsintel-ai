const features = [
  ["NFL Data Lake", "Canonical schedules, teams, players, injuries, venues, odds, and weather."],
  ["LMS Command Center", "Survival probability, future team value, public ownership, and used-team tracking."],
  ["AI Strategy Explorer", "Transparent explanations grounded in normalized sports data."],
];

export default function HomePage() {
  return (
    <main>
      <section className="hero">
        <div className="eyebrow">NFL-first intelligence platform</div>
        <h1>SportsIntel AI</h1>
        <p>
          Explore NFL analytics, model-driven strategies, and Last Man Standing decisions
          with transparent reasoning.
        </p>
        <div className="actions">
          <a href="/lms">Open LMS Command Center</a>
          <a className="secondary" href="/api/v1/platform/readiness">Platform Readiness</a>
        </div>
      </section>

      <section className="grid">
        {features.map(([title, text]) => (
          <article key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
