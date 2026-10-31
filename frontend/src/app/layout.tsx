import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tiger Research Buddy | Research workspace',
  description: 'Find research evidence, collaborate on proposals, and review cited drafts.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
