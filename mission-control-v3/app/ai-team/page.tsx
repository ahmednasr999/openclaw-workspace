import { Shell } from "@/components/shell";
import { Panel } from "@/components/ui";

const team = [
  ["NASR", "Strategic lead", "Active"],
  ["CV Optimizer", "Role tailoring", "Idle"],
  ["Job Hunter", "Pipeline radar", "Active"],
  ["Content Creator", "Thought leadership", "Active"],
];

export default function AITeamPage() {
  return (
    <Shell title="AI Team View" description="Agent roster, ownership, and activity state.">
      <Panel title="Agent status board">
        <div className="overflow-auto">
          <table className="w-full text-left text-sm text-zinc-300">
            <thead className="text-zinc-500">
              <tr>
                <th className="pb-2">Agent</th>
                <th className="pb-2">Focus</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {team.map(([name, focus, status]) => (
                <tr key={name} className="border-t border-zinc-800">
                  <td className="py-2">{name}</td>
                  <td className="py-2">{focus}</td>
                  <td className="py-2">{status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </Shell>
  );
}
