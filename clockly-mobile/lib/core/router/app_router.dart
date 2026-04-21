import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/shell/main_shell.dart';
import '../../features/dashboard/screens/dashboard_screen.dart';
import '../../features/attendance/screens/attendance_screen.dart';
import '../../features/attendance/screens/attendance_history_screen.dart';
import '../../features/employees/screens/employees_screen.dart';
import '../../features/tickets/screens/tickets_screen.dart';
import '../../features/tickets/screens/create_ticket_screen.dart';
import '../../features/tickets/screens/ticket_detail_screen.dart';
import '../../features/business/screens/business_selector_screen.dart';
import '../../features/kiosk/screens/kiosk_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import '../../features/subscriptions/screens/subscriptions_screen.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _shellNavigatorKey = GlobalKey<NavigatorState>();

final routerProvider = Provider<GoRouter>((ref) {
  final authListenable = ValueNotifier<Object?>(null);

  ref.listen(authProvider, (_, next) {
    authListenable.value = next;
  });

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    refreshListenable: authListenable,
    initialLocation: '/attendance',
    redirect: (context, state) {
      final auth = ref.read(authProvider).valueOrNull;

      // Still initializing
      if (auth == null || !auth.isInitialized) return null;

      final isLoginRoute = state.matchedLocation == '/login';

      if (!auth.isAuthenticated && !isLoginRoute) return '/login';
      if (auth.isAuthenticated && isLoginRoute) return '/attendance';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: '/kiosk',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, __) => const KioskScreen(),
      ),
      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/attendance',
            builder: (_, __) => const AttendanceScreen(),
          ),
          GoRoute(
            path: '/attendance/history',
            builder: (_, __) => const AttendanceHistoryScreen(),
          ),
          GoRoute(
            path: '/dashboard',
            builder: (_, __) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/employees',
            builder: (_, __) => const EmployeesScreen(),
          ),
          GoRoute(
            path: '/tickets',
            builder: (_, __) => const TicketsScreen(),
          ),
          GoRoute(
            path: '/tickets/create',
            builder: (_, __) => const CreateTicketScreen(),
          ),
          GoRoute(
            path: '/tickets/:id',
            builder: (_, state) {
              final id = int.parse(state.pathParameters['id']!);
              return TicketDetailScreen(ticketId: id);
            },
          ),
          GoRoute(
            path: '/business',
            builder: (_, __) => const BusinessSelectorScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (_, __) => const SettingsScreen(),
          ),
          GoRoute(
            path: '/subscriptions',
            builder: (_, __) => const SubscriptionsScreen(),
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Página no encontrada: ${state.error}'),
      ),
    ),
  );
});
