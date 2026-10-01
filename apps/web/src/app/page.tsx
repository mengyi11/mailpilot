import { AppLayout } from "@/components/layout/app-layout";
import { InboxPage } from "@/components/mail/inbox-page";

export default function Home() {
  return (
    <AppLayout>
      <InboxPage />
    </AppLayout>
  );
}
