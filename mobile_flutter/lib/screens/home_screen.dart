import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
import '../widgets/attendance_status_card.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final status = state.attendanceStatus;
    final active = status?.isClockedIn ?? false;

    return Scaffold(
      appBar: AppBar(
        title: Text(state.session?.activeBusiness?.name ?? 'Mi fichaje'),
        actions: [
          IconButton(
            onPressed: state.loading ? null : state.refreshAttendance,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: state.refreshAttendance,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            AttendanceStatusCard(status: status),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: state.loading
                  ? null
                  : active
                      ? () => _clockOut(context)
                      : state.clockIn,
              icon: Icon(active ? Icons.logout : Icons.login),
              label: Text(active ? 'Fichar salida' : 'Fichar entrada'),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
                backgroundColor: active ? Colors.red.shade700 : Colors.green.shade700,
              ),
            ),
            if (state.error != null) ...[
              const SizedBox(height: 16),
              Text(
                state.error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _clockOut(BuildContext context) async {
    final noteController = TextEditingController();
    final note = await showDialog<String>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Fichar salida'),
          content: TextField(
            controller: noteController,
            decoration: const InputDecoration(
              labelText: 'Nota opcional',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(noteController.text),
              child: const Text('Confirmar'),
            ),
          ],
        );
      },
    );
    noteController.dispose();
    if (note == null || !context.mounted) return;
    await context.read<AppState>().clockOut(exitNote: note.trim());
  }
}
