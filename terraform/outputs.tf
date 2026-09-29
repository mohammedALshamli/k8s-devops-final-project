output "public_ips" {
  description = "Public IP of each node"
  value       = { for k, v in azurerm_public_ip.pip : k => v.ip_address }
}

output "private_ips" {
  description = "Private IP of each node"
  value       = { for k, n in var.nodes : k => n.private_ip }
}

output "ssh_commands" {
  description = "Ready-to-use SSH commands"
  value = {
    for k, v in azurerm_public_ip.pip :
    k => "ssh -i ~/.ssh/k8slab_key ${var.admin_username}@${v.ip_address}"
  }
}
