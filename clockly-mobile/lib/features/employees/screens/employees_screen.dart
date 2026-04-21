import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../domain/entities/employee_entity.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/premium_components.dart';
import '../../../shared/widgets/user_avatar.dart';
import '../../attendance/providers/attendance_provider.dart';
import '../providers/employees_provider.dart';

class EmployeesScreen extends ConsumerWidget {
  const EmployeesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncState = ref.watch(employeesProvider);
    final attendanceState = ref.watch(attendanceProvider).valueOrNull;

    return Scaffold(
      body: ClocklyBackground(
        child: SafeArea(
          bottom: false,
          child: asyncState.when(
            loading: () => const Center(
              child: CircularProgressIndicator(color: AppColors.cobaltLight),
            ),
            error: (e, _) => ErrorView(
              message: e.toString(),
              onRetry: () => ref.invalidate(employeesProvider),
            ),
            data: (state) => _EmployeesBody(
              state: state,
              activeUserIds: {
                for (final status in attendanceState?.statuses ?? [])
                  if (status.isClockedIn) status.userId,
              },
              onSearch: (q) => ref.read(employeesProvider.notifier).setSearch(q),
              onRefresh: () => ref.read(employeesProvider.notifier).refresh(),
            ),
          ),
        ),
      ),
    );
  }
}

class _EmployeesBody extends StatelessWidget {
  const _EmployeesBody({
    required this.state,
    required this.activeUserIds,
    required this.onSearch,
    required this.onRefresh,
  });

  final EmployeesState state;
  final Set<int> activeUserIds;
  final ValueChanged<String> onSearch;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final employees = state.filtered.map((e) => e.toEntity()).toList();
    final total = state.employees.length;
    final activeAccounts = state.employees.where((e) => e.isActive).length;

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(22, 10, 22, 126),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                const _EmployeesHeader(),
                const SizedBox(height: AppSpacing.x2),
                _TeamSummary(
                  total: total,
                  activeAccounts: activeAccounts,
                  clockedIn: activeUserIds.length,
                ),
                const SizedBox(height: AppSpacing.lg),
                _SearchBox(onChanged: onSearch),
                const SizedBox(height: AppSpacing.lg),
                if (state.loading)
                  const Padding(
                    padding: EdgeInsets.only(top: 110),
                    child: Center(
                      child: CircularProgressIndicator(
                        color: AppColors.cobaltLight,
                      ),
                    ),
                  )
                else if (employees.isEmpty)
                  const EmptyState(
                    title: 'Sin empleados',
                    subtitle: 'No se encontraron empleados con ese criterio.',
                    icon: Icons.groups_rounded,
                  )
                else
                  ...employees.map(
                    (employee) => Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.md),
                      child: _EmployeeCard(
                        employee: employee,
                        isClockedIn: activeUserIds.contains(employee.id),
                        onTap: () => _showEmployeeDetail(context, employee),
                      ),
                    ),
                  ),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  void _showEmployeeDetail(BuildContext context, EmployeeEntity employee) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: AppColors.paper,
          borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        ),
        padding: const EdgeInsets.fromLTRB(22, 12, 22, 26),
        child: SafeArea(
          top: false,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 42,
                  height: 5,
                  margin: const EdgeInsets.only(bottom: AppSpacing.xl),
                  decoration: BoxDecoration(
                    color: AppColors.neutral300,
                    borderRadius: BorderRadius.circular(AppRadius.pill),
                  ),
                ),
              ),
              Row(
                children: [
                  UserAvatar(
                    initials: employee.initials,
                    imageUrl: employee.avatarUrl,
                    size: 52,
                    color: _roleColor(employee.role),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          employee.fullName,
                          style: Theme.of(ctx).textTheme.headlineSmall,
                        ),
                        Text(
                          employee.identifier,
                          style: Theme.of(ctx).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),
              PremiumCard(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Column(
                  children: [
                    InfoRow(
                      icon: Icons.badge_rounded,
                      label: 'Rol',
                      value: employee.roleLabel,
                      color: _roleColor(employee.role),
                    ),
                    InfoRow(
                      icon: Icons.power_settings_new_rounded,
                      label: 'Cuenta',
                      value: employee.isActive ? 'Activa' : 'Inactiva',
                      color: employee.isActive
                          ? AppColors.verde
                          : AppColors.neutral500,
                    ),
                    if (employee.email != null && employee.email!.isNotEmpty)
                      InfoRow(
                        icon: Icons.email_rounded,
                        label: 'Email',
                        value: employee.email!,
                      ),
                    if (employee.weeklyHours != null)
                      InfoRow(
                        icon: Icons.schedule_rounded,
                        label: 'Horas semanales',
                        value: '${employee.weeklyHours!.toStringAsFixed(1)}h',
                        color: AppColors.amber,
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmployeesHeader extends StatelessWidget {
  const _EmployeesHeader();

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
                'Equipo',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              Text(
                'Personas, roles y presencia',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.58),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _TeamSummary extends StatelessWidget {
  const _TeamSummary({
    required this.total,
    required this.activeAccounts,
    required this.clockedIn,
  });

  final int total;
  final int activeAccounts;
  final int clockedIn;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: GlassCard(
            child: _SummaryMetric(
              value: total.toString(),
              label: 'Total',
              color: AppColors.cobaltLight,
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: GlassCard(
            child: _SummaryMetric(
              value: activeAccounts.toString(),
              label: 'Activos',
              color: AppColors.verde,
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: GlassCard(
            child: _SummaryMetric(
              value: clockedIn.toString(),
              label: 'Dentro',
              color: AppColors.amber,
            ),
          ),
        ),
      ],
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.value,
    required this.label,
    required this.color,
  });

  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: AppColors.paper,
              ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: color,
              ),
        ),
      ],
    );
  }
}

class _SearchBox extends StatelessWidget {
  const _SearchBox({required this.onChanged});

  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
      child: TextField(
        onChanged: onChanged,
        decoration: const InputDecoration(
          hintText: 'Buscar empleado...',
          prefixIcon: Icon(Icons.search_rounded),
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
          filled: false,
          contentPadding: EdgeInsets.symmetric(vertical: 14),
        ),
      ),
    );
  }
}

class _EmployeeCard extends StatelessWidget {
  const _EmployeeCard({
    required this.employee,
    required this.isClockedIn,
    required this.onTap,
  });

  final EmployeeEntity employee;
  final bool isClockedIn;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final roleColor = _roleColor(employee.role);

    return PremiumCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      onTap: onTap,
      child: Row(
        children: [
          UserAvatar(
            initials: employee.initials,
            imageUrl: employee.avatarUrl,
            color: roleColor,
            size: 46,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  employee.fullName,
                  style: Theme.of(context).textTheme.titleMedium,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  employee.identifier,
                  style: Theme.of(context).textTheme.bodySmall,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              StatusPill(
                label: employee.roleLabel,
                color: roleColor,
                compact: true,
              ),
              const SizedBox(height: 6),
              StatusPill(
                label: isClockedIn
                    ? 'Dentro'
                    : employee.isActive
                        ? 'Disponible'
                        : 'Inactivo',
                color: isClockedIn
                    ? AppColors.verde
                    : employee.isActive
                        ? AppColors.neutral500
                        : AppColors.rose,
                compact: true,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

Color _roleColor(EmployeeRole role) {
  return switch (role) {
    EmployeeRole.admin => AppColors.cobalt,
    EmployeeRole.manager => AppColors.amber,
    EmployeeRole.employee => AppColors.neutral500,
  };
}
