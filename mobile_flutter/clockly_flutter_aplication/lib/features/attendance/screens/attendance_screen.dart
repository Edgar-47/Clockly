import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/utils/date_utils.dart';
import '../../../shared/extensions/attendance_method_extension.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/error_view.dart';
import '../providers/attendance_provider.dart';
import '../../auth/providers/auth_provider.dart';

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

    if (state.isClockedIn) {
      await _showClockOutDialog();
    } else {
      final ok = await ref.read(attendanceProvider.notifier).clockIn();
      if (ok && mounted) {
        context.showSnackBar('Entrada registrada correctamente');
      }
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
            color: AppColors.surface,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          padding: EdgeInsets.only(
            left: 24,
            right: 24,
            top: 24,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 20),
                decoration: BoxDecoration(
                  color: AppColors.neutral300,
                  borderRadius: BorderRadius.circular(2),
                ),
                alignment: Alignment.center,
              ),
              Text(
                'Registrar salida',
                style: Theme.of(ctx).textTheme.headlineSmall,
              ),
              const SizedBox(height: 20),
              TextField(
                controller: notesController,
                decoration: const InputDecoration(
                  labelText: 'Nota (opcional)',
                  hintText: 'Ej: reunión fuera, salida anticipada...',
                  prefixIcon: Icon(Icons.notes_rounded),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedIncident,
                decoration: const InputDecoration(
                  labelText: 'Tipo de incidencia (opcional)',
                  prefixIcon: Icon(Icons.warning_amber_rounded),
                ),
                items: const [
                  DropdownMenuItem(value: null, child: Text('Sin incidencia')),
                  DropdownMenuItem(value: 'early_exit', child: Text('Salida anticipada')),
                  DropdownMenuItem(value: 'overtime', child: Text('Horas extra')),
                  DropdownMenuItem(value: 'other', child: Text('Otra')),
                ],
                onChanged: (v) => setS(() => selectedIncident = v),
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                style: FilledButton.styleFrom(backgroundColor: AppColors.error),
                child: const Text('Confirmar salida'),
              ),
              const SizedBox(height: 8),
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

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.read(attendanceProvider.notifier).refresh(),
        child: asyncState.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => ErrorView(
            message: e.toString(),
            onRetry: () => ref.invalidate(attendanceProvider),
          ),
          data: (state) => _buildBody(context, state, user),
        ),
      ),
    );
  }

  Widget _buildBody(BuildContext context, AttendanceState state, dynamic user) {
    final isClockedIn = state.isClockedIn;
    final activeSession = state.activeSessionEntity;

    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 0,
          floating: true,
          pinned: false,
          backgroundColor: AppColors.background,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hola, ${user?.fullName.split(' ').first ?? 'Usuario'}',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              Text(
                AppDateUtils.formatDateLong(_now),
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: AppColors.textSecondary),
              ),
            ],
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.history_rounded),
              onPressed: () => context.push('/attendance/history'),
              tooltip: 'Historial',
            ),
          ],
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              // Error banner
              if (state.error != null) ...[
                _ErrorBanner(message: state.error!),
                const SizedBox(height: 16),
              ],

              // Clock display
              _ClockWidget(now: _now),
              const SizedBox(height: 32),

              // Status card
              _StatusCard(
                isClockedIn: isClockedIn,
                activeSession: activeSession,
                now: _now,
              ),
              const SizedBox(height: 32),

              // Main action button
              _ClockButton(
                isClockedIn: isClockedIn,
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

class _ClockWidget extends StatelessWidget {
  const _ClockWidget({required this.now});
  final DateTime now;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        children: [
          Text(
            AppDateUtils.formatTime(now),
            style: Theme.of(context).textTheme.displayLarge?.copyWith(
                  fontSize: 64,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -2,
                  color: AppColors.textPrimary,
                ),
          ),
          Text(
            '${now.second.toString().padLeft(2, '0')}s',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textHint,
                ),
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
    required this.now,
  });

  final bool isClockedIn;
  final dynamic activeSession;
  final DateTime now;

  @override
  Widget build(BuildContext context) {
    final statusColor = isClockedIn ? AppColors.clockedIn : AppColors.clockedOut;
    final statusLabel = isClockedIn ? 'En turno' : 'Fuera de turno';
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: statusColor.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: statusColor.withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: statusColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                statusLabel,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: statusColor,
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ],
          ),
          if (isClockedIn && activeSession != null) ...[
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _SessionStat(
                  label: 'Entrada',
                  value: AppDateUtils.formatTime(activeSession.clockIn),
                ),
                _SessionStat(
                  label: 'Tiempo',
                  value: AppDateUtils.formatDuration(activeSession.effectiveDuration),
                ),
                _SessionStat(
                  label: 'Método',
                  value: activeSession.method.label,
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

}

class _SessionStat extends StatelessWidget {
  const _SessionStat({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall,
        ),
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
    final color = isClockedIn ? AppColors.error : AppColors.clockedIn;
    final label = isClockedIn ? 'Registrar salida' : 'Registrar entrada';
    final icon = isClockedIn ? Icons.logout_rounded : Icons.login_rounded;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        height: 80,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.35),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Center(
          child: loading
              ? const CircularProgressIndicator(color: Colors.white, strokeWidth: 3)
              : Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon, color: Colors.white, size: 28),
                    const SizedBox(width: 12),
                    Text(
                      label,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.errorLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.error.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text(message,
                style: const TextStyle(
                    color: AppColors.error,
                    fontSize: 13,
                    fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}
