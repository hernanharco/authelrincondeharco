/**
 * Utilidades para manejo de fechas y tiempo
 */

export function formatDate(dateString: string): string {
	if (!dateString) return 'N/A';
	const date = new Date(dateString);
	return date.toLocaleDateString('es-ES', {
		day: '2-digit',
		month: '2-digit',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function getRelativeTime(dateString: string): string {
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

export function formatDateTime(dateString: string): string {
	if (!dateString) return 'N/A';
	const date = new Date(dateString);
	return date.toLocaleDateString('es-ES', {
		day: '2-digit',
		month: '2-digit',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit'
	});
}

export function isRecent(dateString: string, hours: number = 24): boolean {
	if (!dateString) return false;
	const date = new Date(dateString);
	const now = new Date();
	const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
	return diffHours < hours;
}
