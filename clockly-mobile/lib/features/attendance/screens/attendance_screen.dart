import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/utils/date_utils.dart';
import '../../../domain/entities/attendance_entity.dart';
import '../../../shared/extensions/attendance_method_extension.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/premium_components.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/attendance_provider.dart';

class AttendanceScreen extends ConsumerStatefulWidget {
  const AttendanceScreen({super.key});

  @override
  ConsumerState<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends ConsumerState<AttendanceScreen> {
  Timer? _ticker;
  DateTime _now = DateTime.now();

  @override
  void initState() {
    super.initState();
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _now = DateTime.now());
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  Future<void> _onClockAction() async {
    final state = ref.read(attendanceProvider).valueOrNull;
    if (state == null) return;

    HapticFeedback.lightImpact();
    if (state.isClockedIn) {
      await _showClockOutDialog();
      return;
    }

    final ok = await ref.read(attendanceProvider.notifier).clockIn();
    if (ok && mounted) {
      HapticFeedback.mediumImpact();
      context.showSnackBar('Entrada registrada correctamente');
    }
  }

  Future<void> _showClockOutDialog() async {
    final notesController = TextEditingController();
    String? selectedIncident;

    final confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => Container(
          decoration: const BoxDecoration(
            color: AppColors.paper,
            borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
          ),
          padding: EdgeInsets.only(
            left: 22,
            right: 22,
            top: 12,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 22,
          ),
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
                  const PremiumIconBox(
                    icon: Icons.logout_rounded,
                    color: AppColors.rose,
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Registrar salida',
                          style: Theme.of(ctx).textTheme.headlineSmall,
                        ),
                        Text(
                          'Cierra tu sesión activa con contexto si hace falta.',
                          style: Theme.of(ctx).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.x2),
              TextField(
                controller: notesController,
                decoration: const InputDecoration(
                  labelText: 'Nota opcional',
                  hintText: 'Reunión fuera, salida anticipada...',
                  prefixIcon: Icon(Icons.notes_rounded),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: AppSpacing.lg),
              DropdownButtonFormField<String>(
                value: selectedIncident,
                decoration: const InputDecoration(
                  labelText: 'Incidencia opcional',
                  prefixIcon: Icon(Icons.warning_amber_rounded),
                ),
                items: const [
                  DropdownMenuItem(value: null, child: Text('Sin incidencia')),
                  DropdownMenuItem(
                    value: 'early_exit',
                    child: Text('Salida anticipada'),
                  ),
                  DropdownMenuItem(value: 'overtime', child: Text('Horas extra')),
                  DropdownMenuItem(value: 'other', child: Text('Otra')),
                ],
                onChanged: (v) => setS(() => selectedIncident = v),
              ),
              const SizedBox(height: AppSpacing.x2),
              FilledButton.icon(
                onPressed: () => Navigator.pop(ctx, true),
                icon: const Icon(Icons.check_rounded),
                label: const Text('Confirmar salida'),
                style: FilledButton.styleFrom(backgroundColor: AppColors.rose),
              ),
              const SizedBox(height: AppSpacing.sm),
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Cancelar'),
              ),
            ],
          ),
        ),
      ),
    );

    if (confirmed == true && mounted) {
      final ok = await ref.read(attendanceProvider.notifier).clockOut(
            notes: notesController.text.trim(),
            incidentType: selectedIncident,
          );
      if (ok && mounted) {
        HapticFeedback.mediumImpact();
        context.showSnackBar('Salida registrada correctamente');
      }
    }
    notesController.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final asyncState = ref.watch(attendanceProvider);
    final auth = ref.watch(authProvider).valueOrNull;
    final user = auth?.session?.userEntity;
    final business = auth?.session?.activeBusiness;

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
              onRetry: () => ref.invalidate(attendanceProvider),
            ),
            data: (state) => RefreshIndicator(
              onRefresh: () => ref.read(attendanceProvider.notifier).refresh(),
              child: _buildBody(context, state, user, business?.name),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody(
    BuildContext context,
    AttendanceState state,
    dynamic user,
    String? businessName,
  ) {
    final activeSession = state.activeSessionEntity;
    final latestSession = state.status?.latestSession?.toEntity();
    final shownSession = activeSession ?? latestSession;

    return CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(22, 10, 22, 126),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _TopBar(
                name: user?.fullName.split(' ').first ?? 'Usuario',
                businessName: businessName ?? 'ClockLy',
                date: AppDateUtils.formatDateLong(_now),
                onHistory: () => context.push('/attendance/history'),
              ),
              const SizedBox(height: AppSpacing.x2),
              _ClockHero(now: _now),
              const SizedBox(height: AppSpacing.x2),
              if (state.error != null) ...[
                _InlineError(message: state.error!),
                const SizedBox(height: AppSpacing.lg),
              ],
              _StatusCard(
                isClockedIn: state.isClockedIn,
                activeSession: activeSession,
                latestSession: latestSession,
                now: _now,
              ),
              const SizedBox(height: AppSpacing.lg),
              _SessionSummary(session: shownSession),
              const SizedBox(height: AppSpacing.x2),
              _ClockButton(
                isClockedIn: state.isClockedIn,
                loading: state.actionLoading,
                onTap: state.actionLoading ? null : _onClockAction,
              ),
            ]),
          ),
        ),
      ],
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({
    required this.name,
    required this.businessName,
    required this.date,
    required this.onHistory,
  });

  final String name;
  final String businessName;
  final String date;
  final VoidCallback onHistory;

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
                'Hola, $name',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              const SizedBox(height: 2),
              Text(
                '$businessName · $date',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.58),
                    ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        IconButton.filled(
          onPressed: onHistory,
          style: IconButton.styleFrom(
            backgroundColor: Colors.white.withOpacity(0.08),
            foregroundColor: AppColors.paper,
          ),
          icon: const Icon(Icons.history_rounded),
          tooltip: 'Historial',
        ),
      ],
    );
  }
}

class _ClockHero extends StatelessWidget {
  const _ClockHero({required this.now});

  final DateTime now;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.fromLTRB(22, 24, 22, 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Ahora',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: Colors.white.withOpacity(0.58),
                ),
          ),
          const SizedBox(height: AppSpacing.sm),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              AppDateUtils.formatTime(now),
              style: const TextStyle(
                color: AppColors.paper,
                fontSize: 72,
                fontWeight: FontWeight.w900,
                height: 0.94,
                letterSpacing: 0,
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              StatusPill(
                label: '${now.second.toString().padLeft(2, '0')} segundos',
                color: AppColors.cobaltLight,
                icon: Icons.timelapse_rounded,
                compact: true,
              ),
              const SizedBox(width: AppSpacing.sm),
              StatusPill(
                label: 'En directo',
                color: AppColors.verde,
                icon: Icons.circle_rounded,
                compact: true,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({
    required this.isClockedIn,
    required this.activeSession,
    required this.latestSession,
    required this.now,
  });

  final bool isClockedIn;
  final AttendanceSessionEntity? activeSession;
  final AttendanceSessionEntity? latestSession;
  final DateTime now;

  @override
  Widget build(BuildContext context) {
    final color = isClockedIn ? AppColors.verde : AppColors.neutral500;
    final label = isClockedIn ? 'Dentro de jornada' : 'Fuera de jornada';
    final helper = isClockedIn && activeSession != null
        ? 'Sesión activa desde ${AppDateUtils.formatTime(activeSession!.clockIn)}'
        : isClockedIn
            ? 'Sesión activa'
        : latestSession != null
            ? 'Última salida registrada'
            : 'Listo para registrar entrada';

    return PremiumCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              PremiumIconBox(
                icon: isClockedIn
                    ? Icons.radio_button_checked_rounded
                    : Icons.radio_button_unchecked_rounded,
                color: color,
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label, style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 3),
                    Text(helper, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
              StatusPill(
                label: isClockedIn ? 'Activo' : 'Cerrado',
                color: color,
                compact: true,
              ),
            ],
          ),
          if (isClockedIn && activeSession != null) ...[
            const SizedBox(height: AppSpacing.xl),
            Row(
              children: [
                Expanded(
                  child: _MiniStat(
                    label: 'Entrada',
                    value: AppDateUtils.formatTime(activeSession!.clockIn),
                  ),
                ),
                Expanded(
                  child: _MiniStat(
                    label: 'Tiempo',
                    value:
                        AppDateUtils.formatDuration(activeSession!.effectiveDuration),
                  ),
                ),
                Expanded(
                  child: _MiniStat(
                    label: 'Método',
                    value: activeSession!.method.label,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _SessionSummary extends StatelessWidget {
  const _SessionSummary({required this.session});

  final AttendanceSessionEntity? session;

  @override
  Widget build(BuildContext context) {
    if (session == null) {
      return PremiumCard(
        color: AppColors.paper,
        child: Row(
          children: [
            const PremiumIconBox(
              icon: Icons.event_available_rounded,
              color: AppColors.cobalt,
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Text(
                'Todavía no hay una sesión reciente para mostrar.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          ],
        ),
      );
    }

    final isActive = session.isActive;
    return PremiumCard(
      color: AppColors.paper,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PremiumSectionHeader(
            title: isActive ? 'Sesión activa' : 'Última sesión',
            subtitle: AppDateUtils.formatDate(session.clockIn),
            action: StatusPill(
              label: _statusLabel(session),
              color: _statusColor(session),
              compact: true,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          InfoRow(
            icon: Icons.login_rounded,
            label: 'Entrada',
            value: AppDateUtils.formatTime(session.clockIn),
            color: AppColors.cobalt,
          ),
          InfoRow(
            icon: Icons.logout_rounded,
            label: 'Salida',
            value: session.clockOut != null
                ? AppDateUtils.formatTime(session.clockOut!)
                : 'Abierta',
            color: session.clockOut != null ? AppColors.neutral500 : AppColors.verde,
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
        ],
      ),
    );
  }

  String _statusLabel(AttendanceSessionEntity session) {
    return switch (session.status) {
      AttendanceStatus.active => 'Abierta',
      AttendanceStatus.manualClose => 'Cierre admin',
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
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w900,
              ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 3),
        Text(label, style: Theme.of(context).textTheme.labelSmall),
      ],
    );
  }
}

class _ClockButton extends StatelessWidget {
  const _ClockButton({
    required this.isClockedIn,
    required this.loading,
    required this.onTap,
  });

  final bool isClockedIn;
  final bool loading;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final color = isClockedIn ? AppColors.rose : AppColors.cobalt;
    final label = isClockedIn ? 'Registrar salida' : 'Registrar entrada';
    final icon = isClockedIn ? Icons.logout_rounded : Icons.login_rounded;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
        height: 76,
        decoration: BoxDecoration(
          color: onTap == null ? AppColors.neutral300 : color,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(onTap == null ? 0 : 0.32),
              blurRadius: 30,
              offset: const Offset(0, 15),
            ),
          ],
        ),
        child: Center(
          child: loading
              ? const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    color: Colors.white,
                    strokeWidth: 3,
                  ),
                )
              : Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon, color: Colors.white, size: 25),
                    const SizedBox(width: AppSpacing.md),
                    Text(
                      label,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.roseSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.rose.withOpacity(0.22)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded,
              color: AppColors.rose, size: 18),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppColors.rose,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
