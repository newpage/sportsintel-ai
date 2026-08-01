import "./styles.css";

export const metadata = {
  title: "SportsIntel AI",
  description: "AI-assisted sports analytics and LMS strategy exploration",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
