import 'package:flutter/material.dart';

import '../models/attendance.dart';

class AttendanceStatusCard extends StatelessWidget {
  const AttendanceStatusCard({super.key, required this.status});

  final AttendanceStatus? status;

  @override
  Widget build(BuildContext context) {
    final active = status?.isClockedIn ?? false;
    final session = status?.activeSession;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              active ? 'En turno' : 'Fuera de turno',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(status?.employee.fullName ?? 'Sin empleado activo'),
            if (session != null) ...[
              const SizedBox(height: 12),
              Text('Entrada: ${_format(session.clockInTime)}'),
            ],
          ],
        ),
      ),
    );
  }

  String _format(DateTime value) {
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}
