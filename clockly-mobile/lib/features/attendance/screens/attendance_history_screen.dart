import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/utils/date_utils.dart';
import '../../../domain/entities/attendance_entity.dart';
import '../../../shared/extensions/attendance_method_extension.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/premium_components.dart';
import '../providers/attendance_provider.dart';

class AttendanceHistoryScreen extends ConsumerStatefulWidget {
  const AttendanceHistoryScreen({super.key});

  @override
  ConsumerState<AttendanceHistoryScreen> createState() =>
      _AttendanceHistoryScreenState();
}

class _AttendanceHistoryScreenState
    extends ConsumerState<AttendanceHistoryScreen> {
  String _activeFilter = 'Todo';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(attendanceProvider.notifier).loadHistory();
    });
  }

  @override
  Widget build(BuildContext context) {
    final asyncState = ref.watch(attendanceProvider);

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
              onRetry: () => ref.read(attendanceProvider.notifier).loadHistory(),
            ),
            data: (state) => RefreshIndicator(
              onRefresh: () => ref.read(attendanceProvider.notifier).loadHistory(),
              child: CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(22, 10, 22, 126),
                    sliver: SliverList(
                      delegate: SliverChildListDelegate([
                        _HistoryHeader(onFilter: _showFilterSheet),
                        const SizedBox(height: AppSpacing.x2),
                        _FilterStrip(activeFilter: _activeFilter),
                        const SizedBox(height: AppSpacing.lg),
                        if (state.loading)
                          const Padding(
                            padding: EdgeInsets.only(top: 120),
                            child: Center(
                              child: CircularProgressIndicator(
                                color: AppColors.cobaltLight,
                              ),
                            ),
                          )
                        else if (state.history.isEmpty)
                          const EmptyState(
                            title: 'Sin registros',
                            subtitle:
                                'No tienes ninguna sesión en el periodo seleccionado.',
                            icon: Icons.history_rounded,
                          )
                        else
                          ...state.history.map((sessionModel) {
                            final session = sessionModel.toEntity();
                            return Padding(
                              padding:
                                  const EdgeInsets.only(bottom: AppSpacing.md),
                              child: _SessionTile(
                                session: session,
                                onTap: () => _showSessionDetail(session),
                              ),
                            );
                          }),
                      ]),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: AppColors.paper,
          borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        ),
        padding: const EdgeInsets.fromLTRB(22, 12, 22, 26),
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
            Text('Filtrar historial',
                style: Theme.of(ctx).textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.lg),
            _FilterOption(
              icon: Icons.today_rounded,
              title: 'Esta semana',
              onTap: () {
                Navigator.pop(ctx);
                setState(() => _activeFilter = 'Semana');
                final from = AppDateUtils.startOfWeek(DateTime.now());
                ref.read(attendanceProvider.notifier).loadHistory(from: from);
              },
            ),
            _FilterOption(
              icon: Icons.calendar_month_rounded,
              title: 'Este mes',
              onTap: () {
                Navigator.pop(ctx);
                setState(() => _activeFilter = 'Mes');
                final from = AppDateUtils.startOfMonth(DateTime.now());
                ref.read(attendanceProvider.notifier).loadHistory(from: from);
              },
            ),
            _FilterOption(
              icon: Icons.history_rounded,
              title: 'Todo',
              onTap: () {
                Navigator.pop(ctx);
                setState(() => _activeFilter = 'Todo');
                ref.read(attendanceProvider.notifier).loadHistory();
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showSessionDetail(AttendanceSessionEntity session) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
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
              PremiumSectionHeader(
                title: 'Detalle de jornada',
                subtitle: AppDateUtils.formatDate(session.clockIn),
                action: StatusPill(
                  label: _statusLabel(session),
                  color: _statusColor(session),
                  compact: true,
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
              PremiumCard(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Column(
                  children: [
                    InfoRow(
                      icon: Icons.login_rounded,
                      label: 'Entrada',
                      value: AppDateUtils.formatTime(session.clockIn),
                    ),
                    InfoRow(
                      icon: Icons.logout_rounded,
                      label: 'Salida',
                      value: session.clockOut == null
                          ? 'Abierta'
                          : AppDateUtils.formatTime(session.clockOut!),
                      color: AppColors.rose,
                    ),
                    InfoRow(
                      icon: Icons.timer_rounded,
                      label: 'Duración',
                      value: AppDateUtils.formatDuration(session.effectiveDuration),
                      color: AppColors.amber,
                    ),
                    InfoRow(
                      icon: Icons.phone_iphone_rounded,
                      label: 'Método',
                      value: session.method.label,
                      color: AppColors.cobalt,
                    ),
                    if (session.notes != null && session.notes!.isNotEmpty)
                      InfoRow(
                        icon: Icons.notes_rounded,
                        label: 'Notas',
                        value: session.notes!,
                        color: AppColors.neutral500,
                      ),
                    if (session.incidentType != null &&
                        session.incidentType!.isNotEmpty)
                      InfoRow(
                        icon: Icons.warning_amber_rounded,
                        label: 'Incidencia',
                        value: session.incidentType!,
                        color: AppColors.amber,
                      ),
                    if (session.closedByAdminReason != null &&
                        session.closedByAdminReason!.isNotEmpty)
                      InfoRow(
                        icon: Icons.admin_panel_settings_rounded,
                        label: 'Cierre admin',
                        value: session.closedByAdminReason!,
                        color: AppColors.rose,
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

class _HistoryHeader extends StatelessWidget {
  const _HistoryHeader({required this.onFilter});

  final VoidCallback onFilter;

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
                'Historial',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              Text(
                'Sesiones, cierres e incidencias',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.58),
                    ),
              ),
            ],
          ),
        ),
        IconButton.filled(
          onPressed: onFilter,
          style: IconButton.styleFrom(
            backgroundColor: Colors.white.withOpacity(0.08),
            foregroundColor: AppColors.paper,
          ),
          icon: const Icon(Icons.tune_rounded),
          tooltip: 'Filtrar',
        ),
      ],
    );
  }
}

class _FilterStrip extends StatelessWidget {
  const _FilterStrip({required this.activeFilter});

  final String activeFilter;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      child: Row(
        children: [
          const Icon(Icons.filter_alt_rounded,
              color: AppColors.cobaltLight, size: 18),
          const SizedBox(width: AppSpacing.sm),
          Text(
            'Periodo',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.white.withOpacity(0.58),
                ),
          ),
          const Spacer(),
          StatusPill(
            label: activeFilter,
            color: AppColors.cobaltLight,
            compact: true,
          ),
        ],
      ),
    );
  }
}

class _SessionTile extends StatelessWidget {
  const _SessionTile({required this.session, required this.onTap});

  final AttendanceSessionEntity session;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = _statusColor(session);

    return PremiumCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      onTap: onTap,
      child: Row(
        children: [
          PremiumIconBox(
            icon: session.isActive
                ? Icons.radio_button_checked_rounded
                : Icons.check_circle_rounded,
            color: color,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AppDateUtils.formatDate(session.clockIn),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 3),
                Text(
                  session.isActive
                      ? 'Entrada ${AppDateUtils.formatTime(session.clockIn)} · abierta'
                      : '${AppDateUtils.formatTime(session.clockIn)} → ${session.clockOut != null ? AppDateUtils.formatTime(session.clockOut!) : '--:--'}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              StatusPill(
                label: _statusLabel(session),
                color: color,
                compact: true,
              ),
              const SizedBox(height: 6),
              Text(
                AppDateUtils.formatDuration(session.effectiveDuration),
                style: Theme.of(context).textTheme.labelMedium,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _FilterOption extends StatelessWidget {
  const _FilterOption({
    required this.icon,
    required this.title,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 4),
      leading: PremiumIconBox(icon: icon, size: 38),
      title: Text(title, style: Theme.of(context).textTheme.titleMedium),
      trailing: const Icon(Icons.chevron_right_rounded),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      onTap: onTap,
    );
  }
}

String _statusLabel(AttendanceSessionEntity session) {
  return switch (session.status) {
    AttendanceStatus.active => 'Abierta',
    AttendanceStatus.manualClose => 'Admin',
    AttendanceStatus.closed => 'Cerrada',
  };
}

Color _statusColor(AttendanceSessionEntity session) {
  return switch (session.status) {
    AttendanceStatus.active => AppColors.verde,
    AttendanceStatus.manualClose => AppColors.amber,
    AttendanceStatus.closed => AppColors.neutral500,
  };
}
