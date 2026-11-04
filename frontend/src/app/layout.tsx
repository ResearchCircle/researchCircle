import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Nexus | The Living Campus Graph',
  description: 'Connecting Minds. Synthesizing Science. Pre-publication campus discovery, private idea protection, and verified proposal studio.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
