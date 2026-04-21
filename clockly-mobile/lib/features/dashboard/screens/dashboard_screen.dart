import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../data/models/dashboard/dashboard_model.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/premium_components.dart';
import '../../../shared/widgets/user_avatar.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/dashboard_provider.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncMetrics = ref.watch(dashboardProvider);
    final auth = ref.watch(authProvider).valueOrNull;
    final business = auth?.session?.activeBusiness;

    return Scaffold(
      body: ClocklyBackground(
        child: SafeArea(
          bottom: false,
          child: asyncMetrics.when(
            loading: () => const Center(
              child: CircularProgressIndicator(color: AppColors.cobaltLight),
            ),
            error: (e, _) => ErrorView(
              message: e.toString(),
              onRetry: () => ref.invalidate(dashboardProvider),
            ),
            data: (metrics) {
              if (metrics == null) {
                return const EmptyState(
                  title: 'Sin datos',
                  subtitle: 'No hay métricas disponibles todavía.',
                  icon: Icons.grid_view_rounded,
                );
              }
              return RefreshIndicator(
                onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
                child: _DashboardBody(
                  metrics: metrics,
                  businessName: business?.name ?? 'Mi empresa',
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({
    required this.metrics,
    required this.businessName,
  });

  final DashboardMetricsModel metrics;
  final String businessName;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(22, 10, 22, 126),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _DashboardHeader(businessName: businessName),
              const SizedBox(height: AppSpacing.x2),
              _KpiGrid(metrics: metrics),
              const SizedBox(height: AppSpacing.x2),
              _AttendanceRateCard(metrics: metrics),
              const SizedBox(height: AppSpacing.x2),
              _QuickActions(),
              if (metrics.pendingTickets > 0) ...[
                const SizedBox(height: AppSpacing.x2),
                _PendingTicketsCard(count: metrics.pendingTickets),
              ],
              if (metrics.employeeHours.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.x2),
                PremiumSectionHeader(
                  title: 'Equipo este mes',
                  subtitle: 'Empleados con más horas registradas',
                  inverse: true,
                ),
                const SizedBox(height: AppSpacing.md),
                ...metrics.employeeHours.take(5).map(
                      (e) => Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                        child: _EmployeeHoursRow(employee: e),
                      ),
                    ),
              ],
            ]),
          ),
        ),
      ],
    );
  }
}

class _DashboardHeader extends StatelessWidget {
  const _DashboardHeader({required this.businessName});

  final String businessName;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const ClocklyBrandLogo(
          variant: ClocklyLogoVariant.mark,
          markSize: 34,
          inverse: true,
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Inicio',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              const SizedBox(height: 2),
              Text(
                businessName,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.58),
                    ),
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _KpiGrid extends StatelessWidget {
  const _KpiGrid({required this.metrics});

  final DashboardMetricsModel metrics;

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: AppSpacing.md,
      mainAxisSpacing: AppSpacing.md,
      childAspectRatio: 1.15,
      children: [
        MetricTile(
          label: 'Horas hoy',
          value: '${metrics.hoursToday.toStringAsFixed(1)}h',
          icon: Icons.today_rounded,
          color: AppColors.cobalt,
        ),
        MetricTile(
          label: 'Semana',
          value: '${metrics.hoursWeek.toStringAsFixed(1)}h',
          icon: Icons.date_range_rounded,
          color: AppColors.amber,
        ),
        MetricTile(
          label: 'Mes',
          value: '${metrics.hoursMonth.toStringAsFixed(1)}h',
          icon: Icons.calendar_month_rounded,
          color: AppColors.verde,
        ),
        MetricTile(
          label: 'Activos ahora',
          value: metrics.activeSessions.toString(),
          icon: Icons.radio_button_checked_rounded,
          color: AppColors.rose,
        ),
      ],
    );
  }
}

class _AttendanceRateCard extends StatelessWidget {
  const _AttendanceRateCard({required this.metrics});

  final DashboardMetricsModel metrics;

  @override
  Widget build(BuildContext context) {
    final total = metrics.totalEmployees;
    final present = metrics.presentToday;
    final rate = total > 0 ? present / total : 0.0;

    return PremiumCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PremiumSectionHeader(
            title: 'Presencia hoy',
            subtitle: '$present de $total empleados dentro',
            action: StatusPill(
              label: '${(rate * 100).toStringAsFixed(0)}%',
              color: AppColors.verde,
              compact: true,
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.pill),
            child: LinearProgressIndicator(
              value: rate.clamp(0, 1),
              minHeight: 10,
              backgroundColor: AppColors.paper2,
              color: AppColors.verde,
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Row(
            children: [
              Expanded(
                child: StatusPill(
                  label: '$present presentes',
                  color: AppColors.verde,
                  icon: Icons.check_rounded,
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: StatusPill(
                  label: '${metrics.absentsToday} fuera',
                  color: AppColors.neutral500,
                  icon: Icons.do_not_disturb_on_rounded,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        PremiumSectionHeader(
          title: 'Accesos rápidos',
          subtitle: 'Gestión mobile-first',
          inverse: true,
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            Expanded(
              child: _QuickActionCard(
                label: 'Equipo',
                icon: Icons.groups_rounded,
                color: AppColors.cobalt,
                onTap: () => context.push('/employees'),
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: _QuickActionCard(
                label: 'Registros',
                icon: Icons.history_rounded,
                color: AppColors.verde,
                onTap: () => context.push('/attendance/history'),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            Expanded(
              child: _QuickActionCard(
                label: 'Tickets',
                icon: Icons.receipt_long_rounded,
                color: AppColors.amber,
                onTap: () => context.push('/tickets'),
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: _QuickActionCard(
                label: 'Negocio',
                icon: Icons.storefront_rounded,
                color: AppColors.rose,
                onTap: () => context.push('/business'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  const _QuickActionCard({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      onTap: onTap,
      child: Row(
        children: [
          PremiumIconBox(icon: icon, color: color, size: 38),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelLarge,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const Icon(
            Icons.chevron_right_rounded,
            color: AppColors.neutral400,
            size: 18,
          ),
        ],
      ),
    );
  }
}

class _PendingTicketsCard extends StatelessWidget {
  const _PendingTicketsCard({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      color: AppColors.amberSoft,
      borderColor: AppColors.amber.withOpacity(0.24),
      onTap: () => context.push('/tickets'),
      child: Row(
        children: [
          const PremiumIconBox(
            icon: Icons.receipt_long_rounded,
            color: AppColors.amber,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$count ${count == 1 ? 'ticket pendiente' : 'tickets pendientes'}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.textPrimary,
                      ),
                ),
                Text(
                  'Requieren revisión',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded, color: AppColors.amber),
        ],
      ),
    );
  }
}

class _EmployeeHoursRow extends StatelessWidget {
  const _EmployeeHoursRow({required this.employee});

  final EmployeeHoursSummaryModel employee;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.md,
      ),
      child: Row(
        children: [
          UserAvatar(initials: _initials(employee.fullName), size: 38),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              employee.fullName,
              style: Theme.of(context).textTheme.titleMedium,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (employee.isClockedIn) ...[
            const SizedBox(width: AppSpacing.sm),
            const StatusPill(
              label: 'Dentro',
              color: AppColors.verde,
              compact: true,
            ),
          ],
          const SizedBox(width: AppSpacing.sm),
          Text(
            '${employee.hoursThisMonth.toStringAsFixed(1)}h',
            style: Theme.of(context).textTheme.labelLarge,
          ),
        ],
      ),
    );
  }

  String _initials(String name) {
    final parts = name.trim().split(' ');
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    return name.isNotEmpty ? name[0].toUpperCase() : '?';
  }
}
