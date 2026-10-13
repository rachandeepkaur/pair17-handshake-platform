import { Check, Minus } from 'lucide-react'
import Card, { CardHeader } from '../ui/Card'

export default function PermissionMatrix({ matrix }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader
        title="Permission matrix"
        subtitle="Every teammate can view jobs, applicants, events, messages, and analytics. Roles control what they can change."
      />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <caption className="sr-only">What each team role can do</caption>
          <thead className="border-b border-gray-100 bg-gray-50/60 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th scope="col" className="px-5 py-3 font-medium">
                Action
              </th>
              {matrix.roles.map((role) => (
                <th key={role.key} scope="col" className="px-3 py-3 text-center font-medium">
                  {role.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {matrix.permissions.map((permission) => (
              <tr key={permission.key}>
                <th scope="row" className="px-5 py-3 font-normal text-gray-700">
                  {permission.label}
                </th>
                {matrix.roles.map((role) => {
                  const allowed = role.permissions.includes(permission.key)
                  return (
                    <td key={role.key} className="px-3 py-3 text-center">
                      {allowed ? (
                        <Check size={18} className="mx-auto text-emerald-600" aria-label="Allowed" />
                      ) : (
                        <Minus size={18} className="mx-auto text-gray-300" aria-label="Not allowed" />
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
