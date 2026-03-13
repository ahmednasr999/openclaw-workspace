import { Shell } from "@/components/shell";
import { ContactsBoard } from "@/components/contacts-board";

export default function ContactsPage() {
  return (
    <Shell title="Contacts/CRM" description="Relationship map with category-driven filtering.">
      <ContactsBoard />
    </Shell>
  );
}
