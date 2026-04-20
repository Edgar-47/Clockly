import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../data/models/dashboard/dashboard_model.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/stat_card.dart';
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
      body: RefreshIndicator(
        onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
        child: asyncMetrics.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => ErrorView(
            message: e.toString(),
            onRetry: () => ref.invalidate(dashboardProvider),
          ),
          data: (metrics) {
            if (metrics == null) {
              return const EmptyState(
                title: 'Sin datos',
                subtitle: 'No hay métricas disponibles todavía.',
                icon: Icons.dashboard_rounded,
              );
            }
            return _buildDashboard(context, metrics, business?.name ?? 'Mi empresa');
          },
        ),
      ),
    );
  }

  Widget _buildDashboard(
      BuildContext context, DashboardMetricsModel metrics, String businessName) {
    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 0,
          floating: true,
          backgroundColor: AppColors.background,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Dashboard', style: Theme.of(context).textTheme.headlineSmall),
              Text(businessName,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: AppColors.textSecondary)),
            ],
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              // Section: Horas
              _SectionHeader(title: 'Horas trabajadas'),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.3,
                children: [
                  StatCard(
                    title: 'Horas hoy',
                    value: '${metrics.hoursToday.toStringAsFixed(1)}h',
                    icon: Icons.today_rounded,
                    color: AppColors.primary,
                  ),
                  StatCard(
                    title: 'Esta semana',
                    value: '${metrics.hoursWeek.toStringAsFixed(1)}h',
                    icon: Icons.date_range_rounded,
                    color: AppColors.accent,
                  ),
                  StatCard(
                    title: 'Este mes',
                    value: '${metrics.hoursMonth.toStringAsFixed(1)}h',
                    icon: Icons.calendar_month_rounded,
                    color: AppColors.success,
                  ),
                  StatCard(
                    title: 'Activos ahora',
                    value: metrics.activeSessions.toString(),
                    icon: Icons.radio_button_checked_rounded,
                    color: AppColors.warning,
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Section: Presencia
              _SectionHeader(title: 'Presencia hoy'),
              const SizedBox(height: 12),
              _AttendanceRateCard(metrics: metrics),
              const SizedBox(height: 24),

              // Section: Tickets
              if (metrics.pendingTickets > 0) ...[
                _SectionHeader(title: 'Tickets pendientes'),
                const SizedBox(height: 12),
                _PendingTicketsCard(count: metrics.pendingTickets),
                const SizedBox(height: 24),
              ],

              // Section: Empleados con más horas
              if (metrics.employeeHours.isNotEmpty) ...[
                _SectionHeader(title: 'Equipo este mes'),
                const SizedBox(height: 12),
                ...metrics.employeeHours.take(5).map(
                      (e) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
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

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: Theme.of(context)
          .textTheme
          .titleMedium
          ?.copyWith(fontWeight: FontWeight.w700, color: AppColors.textPrimary),
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

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.neutral200),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _Pill(
                        count: present,
                        label: 'Presentes',
                        color: AppColors.success),
                    const SizedBox(width: 8),
                    _Pill(
                        count: metrics.absentsToday,
                        label: 'Ausentes',
                        color: AppColors.neutral400),
                  ],
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: rate.clamp(0, 1),
                    minHeight: 8,
                    backgroundColor: AppColors.neutral100,
                    color: AppColors.success,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '${(rate * 100).toStringAsFixed(0)}% asistencia · $total empleados',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.count, required this.label, required this.color});
  final int count;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(
            fontSize: 12, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }
}

class _PendingTicketsCard extends StatelessWidget {
  const _PendingTicketsCard({required this.count});
  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.warningLight,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.warning.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.warning.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.receipt_long_rounded,
                color: AppColors.warning, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$count ${count == 1 ? 'ticket pendiente' : 'tickets pendientes'}',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(color: AppColors.warning),
                ),
                Text(
                  'Requieren tu revisión',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const Icon(Icons.arrow_forward_ios_rounded,
              size: 14, color: AppColors.warning),
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
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.neutral200),
      ),
      child: Row(
        children: [
          UserAvatar(initials: _initials(employee.fullName), size: 36),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              employee.fullName,
              style: Theme.of(context).textTheme.titleMedium,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (employee.isClockedIn)
            Container(
              width: 8,
              height: 8,
              margin: const EdgeInsets.only(right: 8),
              decoration: const BoxDecoration(
                color: AppColors.clockedIn,
                shape: BoxShape.circle,
              ),
            ),
          Text(
            '${employee.hoursThisMonth.toStringAsFixed(1)}h',
            style: Theme.of(context)
                .textTheme
                .labelLarge
                ?.copyWith(fontWeight: FontWeight.w700),
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
