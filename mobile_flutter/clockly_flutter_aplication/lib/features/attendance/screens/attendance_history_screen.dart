import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/utils/date_utils.dart';
import '../../../domain/entities/attendance_entity.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';
import '../providers/attendance_provider.dart';

class AttendanceHistoryScreen extends ConsumerStatefulWidget {
  const AttendanceHistoryScreen({super.key});

  @override
  ConsumerState<AttendanceHistoryScreen> createState() =>
      _AttendanceHistoryScreenState();
}

class _AttendanceHistoryScreenState
    extends ConsumerState<AttendanceHistoryScreen> {
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
      appBar: AppBar(
        title: const Text('Historial'),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list_rounded),
            onPressed: _showFilterSheet,
            tooltip: 'Filtrar',
          ),
        ],
      ),
      body: asyncState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.read(attendanceProvider.notifier).loadHistory(),
        ),
        data: (state) {
          if (state.loading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.history.isEmpty) {
            return const EmptyState(
              title: 'Sin registros',
              subtitle: 'No tienes ninguna sesión en el periodo seleccionado.',
              icon: Icons.history_rounded,
            );
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(attendanceProvider.notifier).loadHistory(),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: state.history.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (ctx, i) {
                final session = state.history[i].toEntity();
                return _SessionTile(session: session);
              },
            ),
          );
        },
      ),
    );
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Filtrar historial',
                style: Theme.of(ctx).textTheme.headlineSmall),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.today_rounded),
              title: const Text('Esta semana'),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              onTap: () {
                Navigator.pop(ctx);
                final from = AppDateUtils.startOfWeek(DateTime.now());
                ref.read(attendanceProvider.notifier).loadHistory(from: from);
              },
            ),
            ListTile(
              leading: const Icon(Icons.calendar_month_rounded),
              title: const Text('Este mes'),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              onTap: () {
                Navigator.pop(ctx);
                final from = AppDateUtils.startOfMonth(DateTime.now());
                ref.read(attendanceProvider.notifier).loadHistory(from: from);
              },
            ),
            ListTile(
              leading: const Icon(Icons.history_rounded),
              title: const Text('Todo'),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              onTap: () {
                Navigator.pop(ctx);
                ref.read(attendanceProvider.notifier).loadHistory();
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _SessionTile extends StatelessWidget {
  const _SessionTile({required this.session});
  final AttendanceSessionEntity session;

  @override
  Widget build(BuildContext context) {
    final color = session.isActive ? AppColors.clockedIn : AppColors.neutral400;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.neutral200),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              session.isActive
                  ? Icons.radio_button_checked_rounded
                  : Icons.check_circle_rounded,
              color: color,
              size: 20,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AppDateUtils.formatDate(session.clockIn),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 2),
                Text(
                  session.isActive
                      ? 'Entrada: ${AppDateUtils.formatTime(session.clockIn)} · Activo'
                      : '${AppDateUtils.formatTime(session.clockIn)} → ${session.clockOut != null ? AppDateUtils.formatTime(session.clockOut!) : '--:--'}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          if (!session.isActive)
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.neutral100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                AppDateUtils.formatDuration(session.effectiveDuration),
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
        ],
      ),
    );
  }
}
