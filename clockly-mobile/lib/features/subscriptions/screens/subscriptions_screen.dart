import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../auth/providers/auth_provider.dart';

class SubscriptionsScreen extends ConsumerWidget {
  const SubscriptionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider).valueOrNull;
    final currentPlan = auth?.session?.activeBusiness?.plan ?? 'free';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Suscripción'),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _CurrentPlanBanner(plan: currentPlan),
          const SizedBox(height: 24),
          Text('Planes disponibles',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          _PlanCard(
            plan: 'free',
            title: 'Free',
            price: '€0',
            color: AppColors.planFree,
            current: currentPlan == 'free',
            features: const [
              'Hasta 3 empleados',
              'Fichaje básico',
              'Historial 30 días',
            ],
            limitations: const [
              'Sin dashboard avanzado',
              'Sin tickets/gastos',
              'Sin kiosko',
            ],
          ),
          const SizedBox(height: 12),
          _PlanCard(
            plan: 'pro',
            title: 'Pro',
            price: '€19/mes',
            color: AppColors.planPro,
            current: currentPlan == 'pro',
            popular: true,
            features: const [
              'Hasta 20 empleados',
              'Dashboard completo',
              'Tickets y gastos',
              'Modo kiosko',
              'Geolocalización',
              'Exportación CSV',
              'Historial ilimitado',
            ],
          ),
          const SizedBox(height: 12),
          _PlanCard(
            plan: 'enterprise',
            title: 'Enterprise',
            price: 'Bajo consulta',
            color: AppColors.planEnterprise,
            current: currentPlan == 'enterprise',
            features: const [
              'Empleados ilimitados',
              'API avanzada',
              'Integración nóminas',
              'Múltiples negocios',
              'Soporte prioritario',
              'SLA garantizado',
              'Auditoría completa',
            ],
          ),
        ],
      ),
    );
  }
}

class _CurrentPlanBanner extends StatelessWidget {
  const _CurrentPlanBanner({required this.plan});
  final String plan;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (plan) {
      'pro' => ('Pro', AppColors.planPro),
      'enterprise' => ('Enterprise', AppColors.planEnterprise),
      _ => ('Free', AppColors.planFree),
    };

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color, color.withOpacity(0.7)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Plan actual',
                    style: TextStyle(color: Colors.white70, fontSize: 13)),
                const SizedBox(height: 4),
                Text(label,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.w800)),
              ],
            ),
          ),
          const Icon(Icons.workspace_premium_rounded,
              color: Colors.white, size: 40),
        ],
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({
    required this.plan,
    required this.title,
    required this.price,
    required this.color,
    required this.current,
    required this.features,
    this.limitations = const [],
    this.popular = false,
  });

  final String plan;
  final String title;
  final String price;
  final Color color;
  final bool current;
  final bool popular;
  final List<String> features;
  final List<String> limitations;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: current ? color : AppColors.neutral200,
          width: current ? 2 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: BoxDecoration(
              color: color.withOpacity(0.08),
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(15)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(title,
                              style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w800,
                                  color: color)),
                          if (popular) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 7, vertical: 2),
                              decoration: BoxDecoration(
                                color: color,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text('Popular',
                                  style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700)),
                            ),
                          ],
                        ],
                      ),
                      Text(price,
                          style: TextStyle(
                              fontSize: 15,
                              color: color.withOpacity(0.7),
                              fontWeight: FontWeight.w500)),
                    ],
                  ),
                ),
                if (current)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text('Activo',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w600)),
                  ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                ...features.map(
                  (f) => _FeatureRow(
                      text: f,
                      icon: Icons.check_circle_rounded,
                      color: AppColors.success),
                ),
                ...limitations.map(
                  (l) => _FeatureRow(
                      text: l,
                      icon: Icons.cancel_rounded,
                      color: AppColors.neutral300),
                ),
              ],
            ),
          ),
          if (!current)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: FilledButton(
                onPressed: () {},
                style: FilledButton.styleFrom(backgroundColor: color),
                child: Text('Cambiar a $title'),
              ),
            ),
        ],
      ),
    );
  }
}

class _FeatureRow extends StatelessWidget {
  const _FeatureRow(
      {required this.text, required this.icon, required this.color});
  final String text;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 10),
          Text(text,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: AppColors.textPrimary)),
        ],
      ),
    );
  }
}
