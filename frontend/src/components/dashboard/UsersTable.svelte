<script lang="ts">
	interface User {
		id: number;
		username: string;
		email: string;
		full_name?: string;
		role: string;
		status: string;
		origin?: string;
		avatar_url?: string;
		last_login?: string;
		created_at: string;
		is_locked: boolean;
	}

	interface Props {
		users: User[];
		onUserUpdate?: (userId: number, field: string, value: any) => void;
		onUserDelete?: (userId: number) => void;
		onUserLock?: (userId: number, isLocked: boolean) => void;
	}

	let { users, onUserUpdate, onUserDelete, onUserLock }: Props = $props();

	let searchQuery = $state('');
	let selectedRole = $state('');
	let selectedStatus = $state('');
	let selectedOrigin = $state('');
	let currentPage = $state(1);
	let itemsPerPage = $state(20);

	const roles = ['SUPERADMIN', 'ADMIN', 'MANAGER', 'USER', 'VIEWER', 'NONE'];
	const statuses = ['ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING'];

	// Get unique origins from users
	const origins = $derived(() => {
		const uniqueOrigins = [...new Set(users.map(u => u.origin || 'unknown').filter(Boolean))];
		return uniqueOrigins.sort();
	});

	// Filter users based on search and filters
	const filteredUsers = $derived(() => {
		return users.filter(user => {
			const matchesSearch = !searchQuery || 
				user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
				user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(user.full_name && user.full_name.toLowerCase().includes(searchQuery.toLowerCase()));

			const matchesRole = !selectedRole || user.role === selectedRole;
			const matchesStatus = !selectedStatus || user.status === selectedStatus;
			const matchesOrigin = !selectedOrigin || (user.origin || 'unknown') === selectedOrigin;

			return matchesSearch && matchesRole && matchesStatus && matchesOrigin;
		});
	});

	// Paginate users
	const paginatedUsers = $derived(() => {
		const startIndex = (currentPage - 1) * itemsPerPage;
		const endIndex = startIndex + itemsPerPage;
		return filteredUsers.slice(startIndex, endIndex);
	});

	const totalPages = $derived(() => Math.ceil(filteredUsers.length / itemsPerPage));

	function handleRoleChange(userId: number, newRole: string) {
		if (onUserUpdate) {
			onUserUpdate(userId, 'role', newRole);
		}
	}

	function handleStatusChange(userId: number, newStatus: string) {
		if (onUserUpdate) {
			onUserUpdate(userId, 'status', newStatus);
		}
	}

	function handleLockToggle(userId: number, isLocked: boolean) {
		if (onUserLock) {
			onUserLock(userId, isLocked);
		}
	}

	function handleDelete(userId: number) {
		if (onUserDelete) {
			onUserDelete(userId);
		}
	}

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('es-ES', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric'
		});
	}

	function getRelativeTime(dateString: string): string {
		if (!dateString) return 'Nunca';
		
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

		if (diffHours < 1) return 'hace menos de 1 hora';
		if (diffHours < 24) return `hace ${diffHours} horas`;
		if (diffDays === 1) return 'ayer';
		if (diffDays < 7) return `hace ${diffDays} días`;
		return formatDate(dateString);
	}

	function exportToCSV() {
		const headers = ['ID', 'Username', 'Email', 'Full Name', 'Role', 'Status', 'Origin', 'Last Login', 'Created At', 'Locked'];
		const csvContent = [
			headers.join(','),
			...filteredUsers.map(user => [
				user.id,
				user.username,
				user.email,
				user.full_name || '',
				user.role,
				user.status,
				user.origin || '',
				user.last_login || '',
				user.created_at,
				user.is_locked
			].map(field => `"${field}"`).join(','))
		].join('\n');

		const blob = new Blob([csvContent], { type: 'text/csv' });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
		a.click();
		window.URL.revokeObjectURL(url);
	}
</script>

<div class="space-y-4">
	<!-- Filters -->
	<div class="bg-[#1E2130] border border-[#2D3148] rounded-lg p-4">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
			<div>
				<label class="block text-sm font-medium text-[#9CA3AF] mb-1">Buscar</label>
				<input
					type="text"
					placeholder="Nombre, email, username..."
					bind:value={searchQuery}
					class="w-full px-3 py-2 bg-[#2D3148] border border-[#374151] rounded-lg text-[#F9FAFB] placeholder-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#6366F1] focus:border-transparent"
				/>
			</div>
			
			<div>
				<label class="block text-sm font-medium text-[#9CA3AF] mb-1">Rol</label>
				<select
					bind:value={selectedRole}
					class="w-full px-3 py-2 bg-[#2D3148] border border-[#374151] rounded-lg text-[#F9FAFB] focus:outline-none focus:ring-2 focus:ring-[#6366F1] focus:border-transparent"
				>
					<option value="">Todos los roles</option>
					{#each roles as role}
						<option value={role}>{role}</option>
					{/each}
				</select>
			</div>

			<div>
				<label class="block text-sm font-medium text-[#9CA3AF] mb-1">Estado</label>
				<select
					bind:value={selectedStatus}
					class="w-full px-3 py-2 bg-[#2D3148] border border-[#374151] rounded-lg text-[#F9FAFB] focus:outline-none focus:ring-2 focus:ring-[#6366F1] focus:border-transparent"
				>
					<option value="">Todos los estados</option>
					{#each statuses as status}
						<option value={status}>{status}</option>
					{/each}
				</select>
			</div>

			<div>
				<label class="block text-sm font-medium text-[#9CA3AF] mb-1">Origen</label>
				<select
					bind:value={selectedOrigin}
					class="w-full px-3 py-2 bg-[#2D3148] border border-[#374151] rounded-lg text-[#F9FAFB] focus:outline-none focus:ring-2 focus:ring-[#6366F1] focus:border-transparent"
				>
					<option value="">Todos los orígenes</option>
					{#each origins as origin}
						<option value={origin}>{origin}</option>
					{/each}
				</select>
			</div>

			<div class="flex items-end">
				<button
					onclick={exportToCSV}
					class="w-full px-4 py-2 bg-[#10B981] text-white rounded-lg hover:bg-[#059669] transition-colors"
				>
					Exportar CSV
				</button>
			</div>
		</div>
	</div>

	<!-- Table -->
	<div class="bg-[#1E2130] border border-[#2D3148] rounded-lg overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full">
				<thead>
					<tr class="border-b border-[#2D3148]">
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Usuario</th>
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Email</th>
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Origen</th>
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Rol</th>
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Estado</th>
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Último login</th>
						<th class="text-left py-3 px-4 text-sm font-medium text-[#9CA3AF]">Acciones</th>
					</tr>
				</thead>
				<tbody>
					{#each paginatedUsers as user (user.id)}
						<tr class="border-b border-[#2D3148] hover:bg-[#2D3148]/50">
							<td class="py-3 px-4">
								<div class="flex items-center">
									<UserAvatar 
										src={user.avatar_url} 
										name={user.full_name || user.username}
										size="sm"
										class="mr-3"
									/>
									<div>
										<div class="text-sm font-medium text-[#F9FAFB]">
											{user.full_name || user.username}
										</div>
										<div class="text-xs text-[#9CA3AF]">@{user.username}</div>
									</div>
								</div>
							</td>
							<td class="py-3 px-4 text-sm text-[#9CA3AF]">{user.email}</td>
							<td class="py-3 px-4">
								<OriginBadge origin={user.origin || 'unknown'} />
							</td>
							<td class="py-3 px-4">
								<RoleBadge 
									role={user.role} 
									editable={true}
									onRoleChange={(newRole) => handleRoleChange(user.id, newRole)}
								/>
							</td>
							<td class="py-3 px-4">
								<StatusBadge 
									status={user.status} 
									editable={true}
									onStatusChange={(newStatus) => handleStatusChange(user.id, newStatus)}
								/>
							</td>
							<td class="py-3 px-4 text-sm text-[#9CA3AF]">
								{getRelativeTime(user.last_login)}
							</td>
							<td class="py-3 px-4">
								<div class="flex items-center space-x-2">
									<a
										href={`/dashboard/users/${user.id}`}
										class="text-[#6366F1] hover:text-[#5558E3]"
										title="Ver detalle"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
										</svg>
									</a>
									
									<button
										onclick={() => handleLockToggle(user.id, !user.is_locked)}
										class={user.is_locked ? 'text-[#10B981] hover:text-[#059669]' : 'text-[#F59E0B] hover:text-[#D97706]'}
										title={user.is_locked ? 'Desbloquear' : 'Bloquear'}
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
										</svg>
									</button>
									
									<button
										onclick={() => handleDelete(user.id)}
										class="text-[#EF4444] hover:text-[#DC2626]"
										title="Eliminar"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="border-t border-[#2D3148] px-4 py-3 flex items-center justify-between">
				<div class="text-sm text-[#9CA3AF]">
					Mostrando {paginatedUsers.length} de {filteredUsers.length} usuarios
				</div>
				<div class="flex items-center space-x-2">
					<button
						onclick={() => currentPage = Math.max(1, currentPage - 1)}
						disabled={currentPage === 1}
						class="px-3 py-1 text-sm bg-[#2D3148] border border-[#374151] rounded text-[#F9FAFB] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#374151]"
					>
						Anterior
					</button>
					
					<span class="text-sm text-[#9CA3AF]">
						Página {currentPage} de {totalPages}
					</span>
					
					<button
						onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage === totalPages}
						class="px-3 py-1 text-sm bg-[#2D3148] border border-[#374151] rounded text-[#F9FAFB] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#374151]"
					>
						Siguiente
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
