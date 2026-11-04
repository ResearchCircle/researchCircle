import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tiger Research Buddy | RIT Research Platform',
  description: 'Find RIT research collaborators, explore public evidence, and draft cited proposals with your team.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
